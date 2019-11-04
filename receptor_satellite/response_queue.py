import asyncio


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

