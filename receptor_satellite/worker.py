import asyncio
import json

from . import satellite_api
from .response_queue import ResponseQueue


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

    def fail(self, message):
        queue = self.run.queue
        playbook_run_id = self.run.playbook_run_id
        return asyncio.gather(queue.playbook_run_update(self.name, playbook_run_id, message, self.sequence),
                              queue.playbook_run_finished(self.name, playbook_run_id, False))

    def report_missing(self):
        return asyncio.gather(*[self.fail('This host is not known by Satellite')])

    async def polling_loop(self):
        if self.id is None:
            await self.report_missing()
            return
        while True:
            await asyncio.sleep(self.run.config.text_update_interval / 1000)
            response = await satellite_api.output(self.run.job_invocation_id, self.id)
            if self.run.config.text_updates and response['body']['output']:
                output = "".join(chunk['output'] for chunk in response['body']['output'])
                await self.run.queue.playbook_run_update(self.name, self.run.playbook_run_id, output, self.sequence)
                self.sequence += 1
            if response['body']['complete']:
                await self.run.queue.playbook_run_finished(self.name, self.run.playbook_run_id)
                break


class Run:
    def __init__(self, queue, remediation_id, playbook_run_id, account, hosts, playbook, config = {}):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.hosts = [Host(self, None, name) for name in hosts]
        self.playbook = playbook
        self.config = Config.from_raw(config)


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
        print("MARKED QUEUE AS DONE")

    def update_hosts(self, hosts):
        host_map = {host.name: host for host in self.hosts}
        for host in hosts:
            host_map[host['name']].id = host['id']

    def abort(self, error):
        body = str(error)
        return asyncio.gather(*[host.fail(body) for host in self.hosts])


def execute(message):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(Run.from_raw(queue, payload).start())
    return queue
