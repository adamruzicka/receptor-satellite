import asyncio


class RunMonitor:
    def __init__(self):
        self.__runs = {}
        self.__lock = asyncio.Lock()

    async def register(self, run):
        async with self.__lock:
            if run.playbook_run_id in self.__runs:
                return False
            else:
                self.__runs[run.playbook_run_id] = run
                return True

    async def done(self, run):
        async with self.__lock:
            self.__runs[run.playbook_run_id] = True

    async def get(self, playbook_run_id):
        async with self.__lock:
            return self.__runs.get(playbook_run_id)


run_monitor = RunMonitor()
