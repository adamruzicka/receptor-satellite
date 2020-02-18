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

    async def health_check(self, foreman_uuid):
        # Ensure that the Foreman UUID matches the addressed one
        url = f"{self.url}/api/settings?search=name%20%3D%20instance_id"
        response = await self.request("GET", url, {})
        status = sanitize_response(response, 200)
        if status["error"]:
            if status["status"] == -1:
                return dict(
                    result="error",
                    message=f"Receptor could not connect to Satellite: {status['error']}",
                    fifi_status=False,
                    code=1
                )
            else:
                return dict(
                    result="error", message=f"Satellite error: {status['error']}",
                    fifi_status=False, code=2
                )
        try:
            gathered_foreman_uuid = status["body"]["results"][0]["value"]
        except (IndexError, KeyError):
            return dict(result="error", message="Could not verify Satellite UUID.",
                        fifi_status=False, code=3)
        else:
            if foreman_uuid.lower() != gathered_foreman_uuid.lower():
                return dict(
                    result="error",
                    message=f"Receptor is connected to Satellite {gathered_foreman_uuid}",
                    fifi_status=False,
                    code=4
                )

        # Ensure that the Foreman has at least one working smart proxy with Ansible
        url = f"{self.url}/api/statuses"
        response = await self.request("GET", url, {})
        status = sanitize_response(response, 200)
        if status["error"]:
            if status["status"] == -1:
                return dict(
                    result="error",
                    message=f"Receptor could not connect to Satellite: {status['error']}",
                    fifi_status=False,
                    code=1
                )
            else:
                return dict(
                    result="error", 
                    message=f"Satellite error: {status['error']}",
                    fifi_status=False, code=2
                )
        try:
            ansible_proxies = [
                sp
                for sp in status["body"]["results"]["foreman"]["smart_proxies"]
                if "ansible" in sp["features"]
            ]
        except KeyError:
            return dict(
                result="ok", 
                message="Could not verify Smart Proxy status",
                code=5,
                fifi_status=False)
        else:
            if not ansible_proxies:
                return dict(
                    result="ok",
                    message=f"Satellite does not have any Ansible enabled Smart Proxies",
                    code=6,
                    fifi_status=False
                )
            ok_proxies = [sp for sp in ansible_proxies if sp["status"] == "ok"]
            if not ok_proxies:
                return dict(
                    result="ok", 
                    message="Satellite Smart Proxies are offline",
                    code=7,
                    fifi_status=False
                )

        return dict(
            result="ok", 
            message="Satellite online and ready.",
            fifi_status=True,
            code=0
        )

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
