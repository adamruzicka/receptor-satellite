import asyncio
import aiohttp
import functools
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


async def request(method, url, extra_data, queue):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, **extra_data) as response:
                response_payload = dict(status=response.status,
                                        body=await response.text())
        await queue.put(response_payload)
    except Exception as e:
        await queue.put(str(e))
    queue.done = True


def execute(message):
    loop = asyncio.get_event_loop()
    queue = ResponseQueue(loop=loop)
    payload = json.loads(message.raw_payload)
    loop.create_task(request(payload.pop("method"),
                             payload.pop("url"),
                             payload,
                             queue))
    return queue
