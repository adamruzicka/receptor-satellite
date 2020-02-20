import json
import ssl

import aiohttp


HEALTH_CHECK_OK = "ok"
HEALTH_CHECK_ERROR = "error"
HEALTH_OK = 0
HEALTH_NO_CONNECTION = 1
HEALTH_BAD_HTTP_STATUS = 2
HEALTH_UUID_UNKNOWN = 3
HEALTH_UUID_MISMATCH = 4
HEALTH_SP_UNKNOWN = 5
HEALTH_SP_NO_ANSIBLE = 6
HEALTH_SP_OFFLINE = 7
HEALTH_UNCONFIGURED = 8

HEALTH_STATUS_RESULTS = {
    HEALTH_OK: dict(
        result=HEALTH_CHECK_OK, fifi_status=True, message="Satellite online and ready"
    ),
    HEALTH_NO_CONNECTION: dict(
        result=HEALTH_CHECK_ERROR,
        fifi_status=False,
        message="Receptor could not connect to Satellite: {error}",
    ),
    HEALTH_BAD_HTTP_STATUS: dict(
        result=HEALTH_CHECK_ERROR, fifi_status=False, message="Satellite error: {error}"
    ),
    HEALTH_UUID_UNKNOWN: dict(
        result=HEALTH_CHECK_ERROR,
        fifi_status=False,
        message="Could not identify Satellite instance UUID",
    ),
    HEALTH_UUID_MISMATCH: dict(
        result=HEALTH_CHECK_ERROR,
        fifi_status=False,
        message="Satellite reports different instance UUID: {uuid}",
    ),
    HEALTH_SP_UNKNOWN: dict(
        result=HEALTH_CHECK_OK,
        fifi_status=False,
        message="Could not find configured Smart Proxies",
    ),
    HEALTH_SP_NO_ANSIBLE: dict(
        result=HEALTH_CHECK_OK,
        fifi_status=False,
        message="Smart Proxies do not have Ansible support",
    ),
    HEALTH_SP_OFFLINE: dict(
        result=HEALTH_CHECK_OK, fifi_status=False, message="Smart Proxies are offline"
    ),
    HEALTH_UNCONFIGURED: dict(
        result=HEALTH_CHECK_ERROR,
        fifi_status=False,
        message="Satellite plugin not fully configured on Receptor.",
    ),
}


class SatelliteAPI:
    def __init__(self, username, password, url, ca_file, validate_cert=True):
        self.username = username
        self.password = password
        self.url = url
        self.context = None
        self.session = None
        if url.startswith("https"):
            self.context = ssl.SSLContext()
            if ca_file:
                self.context.load_verify_locations(cafile=ca_file)
            if validate_cert:
                self.context.verify_mode = ssl.CERT_REQUIRED

    FALSE_VALUES = ["false", "no", "0", ""]

    @classmethod
    def from_plugin_config(cls, plugin_config):
        validate_cert = plugin_config.get("validate_cert")
        return cls(
            plugin_config["username"],
            plugin_config["password"],
            plugin_config["url"],
            plugin_config.get("ca_file"),
            False if validate_cert in cls.FALSE_VALUES else True,
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

    def health_check_response(self, health_status, msg_context=None):
        to_return = HEALTH_STATUS_RESULTS[health_status].copy()
        to_return["code"] = health_status
        msg_context = msg_context or {}
        to_return["message"] = to_return["message"].format(**msg_context)
        return to_return

    async def health_check(self, satellite_instance_id):
        await self.init_session()
        try:
            # Ensure that the Foreman UUID matches the addressed one
            url = f"{self.url}/api/settings?search=name%20%3D%20instance_id"
            response = await self.request("GET", url, {})
            status = sanitize_response(response, 200)
            if status["error"]:
                if status["status"] == -1:
                    return self.health_check_response(HEALTH_NO_CONNECTION, status)
                return self.health_check_response(HEALTH_BAD_HTTP_STATUS, status)
            try:
                gathered_id = status["body"]["results"][0]["value"]
            except (IndexError, KeyError):
                return self.health_check_response(HEALTH_UUID_UNKNOWN)
            if satellite_instance_id.lower() != gathered_id.lower():
                return self.health_check_response(
                    HEALTH_UUID_MISMATCH, dict(uuid=gathered_id)
                )

            # Ensure that the Foreman has at least one working smart proxy with Ansible
            url = f"{self.url}/api/statuses"
            response = await self.request("GET", url, {})
            status = sanitize_response(response, 200)
            if status["error"]:
                if status["status"] == -1:
                    return self.health_check_response(HEALTH_NO_CONNECTION, status)
                else:
                    return self.health_check_response(HEALTH_BAD_HTTP_STATUS, status)
            try:
                ansible_proxies = [
                    sp
                    for sp in status["body"]["results"]["foreman"]["smart_proxies"]
                    if "ansible" in sp["features"]
                ]
            except KeyError:
                return self.health_check_response(HEALTH_SP_UNKNOWN)
            else:
                if not ansible_proxies:
                    return self.health_check_response(HEALTH_SP_NO_ANSIBLE)
                ok_proxies = [sp for sp in ansible_proxies if sp["status"] == "ok"]
                if not ok_proxies:
                    return self.health_check_response(HEALTH_SP_OFFLINE)

            return self.health_check_response(HEALTH_OK)
        finally:
            await self.close_session()

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
