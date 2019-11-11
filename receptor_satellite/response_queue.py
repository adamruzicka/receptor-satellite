import asyncio


class ResponseQueue(asyncio.Queue):

    def __init__(self, *args, **kwargs):
        self.done = False
        super().__init__(*args, **kwargs)

    def __aiter__(self):
        return self

    async def __anext__(self):
        while True:
            try:
                return self.get_nowait()
            except asyncio.QueueEmpty:
                if self.done:
                    raise StopAsyncIteration
            await asyncio.sleep(0.5)

    def ack(self, playbook_run_id):
        payload = {
            'type': 'playbook_run_ack',
            'playbook_run_id': playbook_run_id
        }
        return self.put(payload)

    def playbook_run_update(self, host, playbook_run_id, output, sequence):
        payload = {
            'type': 'playbook_run_update',
            'playbook_run_id': playbook_run_id,
            'sequence': sequence,
            'host': host,
            'console': output
        }
        return self.put(payload)

    def playbook_run_finished(self, host, playbook_run_id, success=True):
        payload = {
            'type': 'playbook_run_finished',
            'playbook_run_id': playbook_run_id,
            'host': host,
            'status': 'success' if success else 'failure'
        }
        return self.put(payload)

