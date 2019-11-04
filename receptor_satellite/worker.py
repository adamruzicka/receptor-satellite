import aiohttp
import asyncio
import json

# TODO: Get this from somewhere
SATELLITE_HOST = 'localhost:3000'


class SatelliteAPI:
    @staticmethod
    async def trigger(queue, inputs, hosts):
        payload = {
            "job_invocation": {
                "feature": "ansible_run_playbook",
                "inputs": inputs,
                "host_ids": "name ^ ({})".format(','.join(hosts))
            }
        }
        url = f'http://{SATELLITE_HOST}/api/v2/job_invocations'
        extra_data = {
            "json": payload,
            "headers": {"Content-Type": "application/json"},
            "auth": aiohttp.BasicAuth("admin", "changeme") # TODO: Handle auth
        }
        response = await request('POST', url, extra_data, queue)
        # TODO: Error checking
        return json.loads(response['body'])


    @staticmethod
    async def output(queue, job_invocation_id, host_id):
        url = 'http://{}/api/v2/job_invocations/{}/hosts/{}'.format(SATELLITE_HOST, job_invocation_id, host_id)
        # TODO: Handle auth
        response = await request('GET', url, {"auth": aiohttp.BasicAuth("admin", "changeme")}, queue)
        print(response)
        # TODO: Error checking
        return json.loads(response['body'])


async def request(method, url, extra_data, queue):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **extra_data) as response:
                return dict(status=response.status,
                            body=await response.text())
    except Exception as e:
        # TODO: Handle this
        await queue.put(str(e))


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

    async def ack(self, playbook_run_id):
        payload = {
            'type': 'playbook_run_ack',
            'playbook_run_id': playbook_run_id
        }
        await self.put(payload)

    async def playbook_run_update(self, host, playbook_run_id, output, sequence):
        payload = {
            'type': 'playbook_run_update',
            'playbook_run_id': playbook_run_id,
            'sequence': sequence,
            'host': host,
            'console': output
        }
        await self.put(payload)

    async def playbook_run_finished(self, host, playbook_run_id):
        payload = {
            'type': 'playbook_run_finished',
            'playbook_run_id': playbook_run_id,
            'host': host,
            'status': 'success' # TODO
        }
        await self.put(payload)


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
        self.hosts = hosts
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
        response = await SatelliteAPI.trigger(self.queue,
                                              {'playbook': self.playbook},
                                              self.hosts)
        print(response)
        self.job_invocation_id = response['id']
        # TODO: In theory Satellite may not know the requested host
        self.hosts = [(host['id'], host['name']) for host in response['targeting']['hosts']]
        await self.queue.ack(self.playbook_run_id)
        await asyncio.gather(*[self.host_polling_loop(host) for host in self.hosts])
        self.queue.done = True
        print("MARKED QUEUE AS DONE")

    async def host_polling_loop(self, host):
        host_id, name = host
        sequence = 0
        while True:
            print(f"POLLING LOOP FOR: {name}")
            await asyncio.sleep(self.config.text_update_interval / 1000)
            response = await SatelliteAPI.output(self.queue, self.job_invocation_id, host_id)
            if self.config.text_updates and not response['output']:
                print(f"POLLING LOOP UPDATE for {name}")
                await self.queue.playbook_run_update(name, self.playbook_run_id, self.response['output'], sequence)
                sequence += 1
            if response['complete']:
                print(f"POLLING LOOP FINISH for {name}")
                await self.queue.playbook_run_finished(name, self.playbook_run_id)
                break


def execute(message):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(Run.from_raw(queue, payload).start())
    return queue
