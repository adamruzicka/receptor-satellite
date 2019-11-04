import aiohttp
import json


# TODO: Get this from somewhere
SATELLITE_HOST = 'localhost:3000'
SATELLITE_USERNAME = 'admin'
SATELLITE_PASSWORD = 'changeme'


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
        "auth": aiohttp.BasicAuth(SATELLITE_USERNAME, SATELLITE_PASSWORD)
    }
    response = await request('POST', url, extra_data, queue)
    # TODO: Error checking
    return json.loads(response['body'])


async def output(queue, job_invocation_id, host_id):
    url = 'http://{}/api/v2/job_invocations/{}/hosts/{}'.format(SATELLITE_HOST, job_invocation_id, host_id)
    # TODO: Handle auth
    response = await request('GET', url, {"auth": aiohttp.BasicAuth(SATELLITE_USERNAME, SATELLITE_PASSWORD)}, queue)
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
