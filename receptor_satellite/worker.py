import asyncio
import aiohttp
# import functools
import json


class ResponseQueue(asyncio.Queue):

    def __init__(self, *args, **kwargs):
        self.done = False
        super().__init__(*args, **kwargs)

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.done:
            raise StopAsyncIteration
        return await self.get()


class Run:
    def __init__(self, queue, remediation_id, playbook_run_id, account, hosts, playbook, config = {}):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.hosts = hosts
        self.playbook = playbook
        self.config = config


    def from_raw(queue, raw):
        return Run(queue,
                   raw['remediation_id'],
                   raw['playbook_run_id'],
                   raw['account'],
                   raw['hosts'],
                   raw['playbook'],
                   raw['config'])


    async def start(self):
        self.trigger()
        self.ack()
        self.queue.done = True


    async def trigger(self):
        payload = {
            "job_invocation": {
                "feature": "ansible_run_playbook",
                "inputs": {
                    "playbook": self.playbook
                },
                "host_ids": "name ^ ({})".format(','.join(self.hosts))
            }
        }
        # TODO: Get Satellite hostname from somewhere (config?)
        url = 'https://localhost:3000/api/v2/job_invocations'
        # TODO: Handle auth
        request('POST',
                url,
                payload,
                self.queue)


    async def ack(self):
        payload = {
            'type': 'playbook_run_ack',
            'playbook_run_id': self.playbook_run_id
        }
        await self.queue.put(payload)


async def request(method, url, extra_data, queue):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **extra_data) as response:
                response_payload = dict(status=response.status,
                                        body=await response.text())
        return response_payload
    except Exception as e:
        # TODO: Handle this
        await queue.put(str(e))


def execute(message):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(Run.from_raw(queue, payload).start())
    return queue
