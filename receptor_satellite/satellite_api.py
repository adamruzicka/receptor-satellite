import aiohttp
import json
import ssl


class SatelliteAPI:
    def __init__(self, username, password, url):
        self.username = username
        self.password = password
        self.url = url
        self.context = None
        if url.startswith('https'):
            self.context = ssl.SSLContext()
            cafile = '/etc/puppetlabs/puppet/ssl/certs/ca.pem'
            self.context.load_verify_locations(cafile=cafile)
            self.context.verify_mode = ssl.CERT_REQUIRED


    @classmethod
    def from_plugin_config(cls, plugin_config):
        return cls(plugin_config['username'],
                   plugin_config['password'],
                   plugin_config['url'])

    async def trigger(self, inputs, hosts):
        payload = {
            "job_invocation": {
                "feature": "ansible_run_playbook",
                "inputs": inputs,
                "host_ids": "name ^ ({})".format(','.join(hosts))
            }
        }
        url = f'{self.url}/api/v2/job_invocations'
        extra_data = {
            "json": payload,
            "headers": {"Content-Type": "application/json"}
        }
        response = await self.request('POST', url, extra_data)
        return sanitize_response(response, 201)


    async def output(self, job_invocation_id, host_id, since):
        url = '{}/api/v2/job_invocations/{}/hosts/{}'.format(self.url, job_invocation_id, host_id)
        extra_data = {"auth": aiohttp.BasicAuth(self.username, self.password)}
        if since is not None:
            extra_data["params"] = {"since": str(since)}
        response = await self.request('GET', url, extra_data)
        return sanitize_response(response, 200)


    async def request(self, method, url, extra_data):
        try:
            async with aiohttp.ClientSession() as session:
                extra_data = {**extra_data, **dict(auth=aiohttp.BasicAuth(self.username, self.password), ssl=self.context)}
                async with session.request(method, url, **extra_data) as response:
                    return dict(status=response.status,
                                body=await response.text(),
                                error=None)
        except Exception as e:
            return dict(error=e, body="{}", status=-1)


def sanitize_response(response, expected_status):
    print(response)
    if not response['error']:
        response['body'] = json.loads(response['body'])
        if response['status'] != expected_status:
            response['error'] = response['body']['error']['message']
    return response
