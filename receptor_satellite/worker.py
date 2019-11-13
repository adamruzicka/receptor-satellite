import asyncio
import json

from . import satellite_api
from .response_queue import ResponseQueue
from .run_monitor import run_monitor


class Config:
    def __init__(self, text_updates = False, text_update_interval = 5000, text_update_full = True):
        self.text_updates = text_updates
        self.text_update_interval = text_update_interval
        self.text_update_full = text_update_full


    @classmethod
    def from_raw(cls, raw = {}):
        return cls(raw['text_updates'], raw['text_update_interval'], raw['text_update_full'])


class Host:
    def __init__(self, run, id, name):
        self.run = run
        self.id = id
        self.name = name
        self.sequence = 0
        self.since = None if run.config.text_update_full else 0.0


    def mark_as_failed(self, message):
        queue = self.run.queue
        playbook_run_id = self.run.playbook_run_id
        return asyncio.gather(queue.playbook_run_update(self.name, playbook_run_id, message, self.sequence),
                              queue.playbook_run_finished(self.name, playbook_run_id, False))


    async def polling_loop(self):
        if self.id is None:
            return await self.mark_as_failed('This host is not known by Satellite')
        while True:
            response = await self.poll_with_retries()
            if response['error']:
                break
            body = response['body']
            if self.run.config.text_updates and body['output']:
                output = "".join(chunk['output'] for chunk in body['output'])
                if self.since is not None:
                    self.since = body['output'][-1]['timestamp']
                await self.run.queue.playbook_run_update(self.name, self.run.playbook_run_id, output, self.sequence)
                self.sequence += 1
            if body['complete']:
                await self.run.queue.playbook_run_finished(self.name, self.run.playbook_run_id)
                break


    async def poll_with_retries(self):
        retry = 0
        while retry < 5:
            await asyncio.sleep(self.run.config.text_update_interval / 1000)
            response = await satellite_api.output(self.run.job_invocation_id, self.id, self.since)
            if response['error'] is None:
                return response
            retry += 1
        await self.mark_as_failed(response['error'])
        return dict(error=True)


class Run:
    def __init__(self, queue, remediation_id, playbook_run_id, account, hosts, playbook, config = {}):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.playbook = playbook
        self.config = Config.from_raw(config)
        self.hosts = [Host(self, None, name) for name in hosts]


    @classmethod
    def from_raw(cls, queue, raw):
        return cls(queue,
                   raw['remediation_id'],
                   raw['playbook_run_id'],
                   raw['account'],
                   raw['hosts'],
                   raw['playbook'],
                   raw['config'])


    async def start(self):
        if not await run_monitor.register(self):
            print(f"Playbook run {self.playbook_run_id} already known, skipping.")
            self.queue.done = True
            return
        response = await satellite_api.trigger({'playbook': self.playbook},
                                               [host.name for host in self.hosts])
        await self.queue.ack(self.playbook_run_id)
        if response['error']:
            await self.abort(response['error'])
        else:
            self.job_invocation_id = response['body']['id']
            self.update_hosts(response['body']['targeting']['hosts'])
            await asyncio.gather(*[host.polling_loop() for host in self.hosts])
        self.queue.done = True
        await run_monitor.done(self)
        print("MARKED QUEUE AS DONE")


    def update_hosts(self, hosts):
        host_map = {host.name: host for host in self.hosts}
        for host in hosts:
            host_map[host['name']].id = host['id']


    def abort(self, error):
        body = str(error)
        return asyncio.gather(*[host.mark_as_failed(body) for host in self.hosts])


def execute(message, config):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(Run.from_raw(queue, payload).start())
    return queue
