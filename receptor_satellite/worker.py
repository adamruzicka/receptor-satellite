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


class Run:
    def __init__(self, queue, remediation_id, playbook_run_id, account, hosts, playbook, config = {}):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.hostnames = hosts
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
                                               self.hostnames)
        print(response)
        await self.queue.ack(self.playbook_run_id)
        if response['error']:
            await self.abort(response['error'])
            self.queue.done = True
            return
        self.job_invocation_id = response['body']['id']
        self.hosts = [(host['id'], host['name']) for host in response['body']['targeting']['hosts']]
        await asyncio.gather(self.handle_missing_hosts(),
                             *[self.host_polling_loop(host) for host in self.hosts])
        self.queue.done = True
        print("MARKED QUEUE AS DONE")

    async def host_polling_loop(self, host):
        host_id, name = host
        sequence = 0
        while True:
            print(f"POLLING LOOP FOR: {name}")
            await asyncio.sleep(self.config.text_update_interval / 1000)
            response = await satellite_api.output(self.job_invocation_id, host_id)
            body = json.loads(response['body'])
            if self.config.text_updates and not body['output']:
                print(f"POLLING LOOP UPDATE for {name}")
                await self.queue.playbook_run_update(name, self.playbook_run_id, body['output'], sequence)
                sequence += 1
            if body['complete']:
                print(f"POLLING LOOP FINISH for {name}")
                await self.queue.playbook_run_finished(name, self.playbook_run_id)
                break

    def abort(self, error):
        body = str(error)
        return asyncio.gather(*[self.fail_host(host, body) for host in self.hostnames])

    def fail_host(self, host, message):
        return asyncio.gather(self.queue.playbook_run_update(host, self.playbook_run_id, message, 0),
                              self.queue.playbook_run_finished(host, self.playbook_run_id, False))


    def handle_missing_hosts(self):
        unknown_hosts = set(self.hostnames) - set([host[1] for host in self.hosts])
        return asyncio.gather(*[self.fail_host(host, 'This host is not known by Satellite') for host in unknown_hosts])


def execute(message):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(Run.from_raw(queue, payload).start())
    return queue
