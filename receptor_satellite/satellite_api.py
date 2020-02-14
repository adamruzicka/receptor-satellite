import aiohttp
import json
import ssl


class SatelliteAPI:
    def __init__(self, username, password, url, ca_file):
        self.username = username
        self.password = password
        self.url = url
        self.context = None
        self.session = None
        if url.startswith("https") and ca_file is not None:
            self.context = ssl.SSLContext()
            self.context.load_verify_locations(cafile=ca_file)
            self.context.verify_mode = ssl.CERT_REQUIRED

    @classmethod
    def from_plugin_config(cls, plugin_config):
        return cls(
            plugin_config["username"],
            plugin_config["password"],
            plugin_config["url"],
            plugin_config.get("ca_file"),
        )

    async def trigger(self, inputs, hosts):
        payload = {
            "job_invocation": {
                "feature": "ansible_run_playbook",
                "inputs": inputs,
                "host_ids": "name ^ ({})".format(",".join(hosts)),
            }
        }
        url = f"{self.url}/api/v2/job_invocations"
        extra_data = {"json": payload, "headers": {"Content-Type": "application/json"}}
        response = await self.request("POST", url, extra_data)
        return sanitize_response(response, 201)

    async def output(self, job_invocation_id, host_id, since):
        url = "{}/api/v2/job_invocations/{}/hosts/{}".format(
            self.url, job_invocation_id, host_id
        )
        extra_data = {"auth": aiohttp.BasicAuth(self.username, self.password)}
        if since is not None:
            extra_data["params"] = {"since": str(since)}
        response = await self.request("GET", url, extra_data)
        return sanitize_response(response, 200)

    async def request(self, method, url, extra_data):
        try:
            extra_data["ssl"] = self.context
            async with self.session.request(method, url, **extra_data) as response:
                return dict(
                    status=response.status, body=await response.text(), error=None
                )
        except Exception as e:
            return dict(error=e, body="{}", status=-1)

    async def init_session(self):
        auth = aiohttp.BasicAuth(self.username, self.password)
        self.session = aiohttp.ClientSession(auth=auth)

    async def close_session(self):
        await self.session.close()
        self.session = None


def sanitize_response(response, expected_status):
    if not response["error"]:
        response["body"] = json.loads(response["body"])
        if response["status"] != expected_status:
            response["error"] = response["body"]["error"]["message"]
    return response
