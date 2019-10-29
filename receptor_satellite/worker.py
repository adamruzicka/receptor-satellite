import aiohttp
import asyncio
import json

# TODO: Get this from somewhere
SATELLITE_HOST = 'localhost:3000'


class SatelliteAPI:
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


    async def output(queue, host):
        url = 'http://{}/api/v2/job_invocations/{}/hosts/{}'.format(SATELLITE_HOST, host.run.job_invocation_id, host.id)
        # TODO: Handle auth
        response = await request('GET', url, {"auth": aiohttp.BasicAuth("admin", "changeme")}, queue)
        print(response)
        # TODO: Error checking
        return json.loads(response['body'])


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

    async def playbook_run_update(self, host, output):
        payload = {
            'type': 'playbook_run_update',
            'playbook_run_id': host.run.playbook_run_id,
            'sequence': host.sequence,
            'host': host.name,
            'console': output
        }
        await self.put(payload)

    async def playbook_run_finished(self, host):
        payload = {
            'type': 'playbook_run_finished',
            'playbook_run_id': host.run.playbook_run_id,
            'host': host.name,
            'status': 'success' # TODO
        }
        await self.put(payload)


class Config:
    def __init__(self, text_updates = False, text_update_interval = 5000, text_update_full = True):
        self.text_updates = text_updates
        self.text_update_interval = text_update_interval
        self.text_update_full = text_update_full


    def from_raw(raw = {}):
        return Config(raw['text_updates'], raw['text_update_interval'], raw['text_update_full'])


class Host:
    def __init__(self, id, name, run):
        self.id = id
        self.name = name
        self.run = run
        self.sequence = 0


    async def polling_loop(self):
        while True:
            print(f"POLLING LOOP FOR: {self.name}")
            await asyncio.sleep(self.run.config.text_update_interval / 1000)
            response = await SatelliteAPI.output(self.run.queue, self)
            if self.run.config.text_updates and not response['output']:
                print(f"POLLING LOOP UPDATE for {self.name}")
                await self.run.queue.playbook_run_update(self, response['output'])
                self.sequence += 1
            if response['complete']:
                print(f"POLLING LOOP FINISH for {self.name}")
                await self.run.queue.playbook_run_finished(self)
                break


class Run:
    def __init__(self, queue, remediation_id, playbook_run_id, account, hosts, playbook, config = {}):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.hosts = [Host(None, host, self) for host in hosts]
        self.playbook = playbook
        self.config = Config.from_raw(config)


    def from_raw(queue, raw):
        return Run(queue,
                   raw['remediation_id'],
                   raw['playbook_run_id'],
                   raw['account'],
                   raw['hosts'],
                   raw['playbook'],
                   raw['config'])


    async def start(self):
        response = await SatelliteAPI.trigger(self.queue,
                                              {'playbook': self.playbook},
                                              [host.name for host in self.hosts])
        print(response)
        self.job_invocation_id = response['id']
        self.update_hosts(response['targeting']['hosts'])
        await self.queue.ack(self.playbook_run_id)
        for coroutine in [host.polling_loop() for host in self.hosts]:
            await coroutine
        self.queue.done = True


    def update_hosts(self, hosts):
        hosts = {host['name']: host['id'] for host in hosts}
        for host in self.hosts:
            if host.name in hosts:
                host.id = hosts[host.name]
            # TODO: In theory Satellite may not know the request host


def execute(message):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(Run.from_raw(queue, payload).start())
    return queue
