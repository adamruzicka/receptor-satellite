import asyncio
import json
import logging

from .satellite_api import SatelliteAPI, HEALTH_CHECK_ERROR, HEALTH_STATUS_RESULTS
from .response.response_queue import ResponseQueue
import receptor_satellite.response.constants as constants
from .run_monitor import run_monitor


def receptor_export(func):
    setattr(func, "receptor_export", True)
    return func


def configure_logger():
    logger = logging.getLogger(__name__)
    receptor_logger = logging.getLogger("receptor")
    logger.setLevel(receptor_logger.level)
    for handler in receptor_logger.handlers:
        logger.addHandler(handler)
    return logger


def validate(condition, value, default_value, error, logger):
    if condition(value):
        return value
    else:
        if value is not None:
            logger.warning(error)
        return default_value


class Config:
    class Defaults:
        TEXT_UPDATES = False
        TEXT_UPDATE_INTERVAL = 5000
        TEXT_UPDATE_FULL = True

    def __init__(self, text_updates, text_update_interval, text_update_full):
        self.text_updates = text_updates
        self.text_update_interval = (
            text_update_interval // 1000
        )  # Store the interval in seconds
        self.text_update_full = text_update_full

    @classmethod
    def from_raw(cls, raw={}):
        return cls(
            raw["text_updates"], raw["text_update_interval"], raw["text_update_full"]
        )

    @classmethod
    def validate_input(_cls, raw, logger):
        text_updates = raw.get("text_updates")
        text_update_interval = raw.get("text_update_interval")
        text_update_full = raw.get("text_update_full")

        validated = {}
        validated["text_updates"] = validate(
            lambda val: type(val) == bool,
            text_updates,
            Config.Defaults.TEXT_UPDATES,
            f"Expected the value of text_updates '{text_updates}' to be a boolean",
            logger,
        )
        validated["text_update_full"] = validate(
            lambda val: type(val) == bool,
            text_update_full,
            Config.Defaults.TEXT_UPDATE_FULL,
            f"Expected the value of text_update_full '{text_update_full}' to be a boolean",
            logger,
        )
        validated["text_update_interval"] = validate(
            lambda val: type(val) == int and val >= 5000,
            text_update_interval,
            Config.Defaults.TEXT_UPDATE_INTERVAL,
            f"Expected the value of text_update_interval '{text_update_interval}' to be an integer greater or equal than 5000",
            logger,
        )
        return validated


class Host:
    def __init__(self, run, id, name):
        self.run = run
        self.id = id
        self.name = name
        self.sequence = 0
        self.since = None if run.config.text_update_full else 0.0

    def mark_as_failed(self, message):
        queue = self.run.queue
        playbook_run_id = self.run.playbook_run_id
        queue.playbook_run_update(self.name, playbook_run_id, message, self.sequence)
        queue.playbook_run_finished(
            self.name, playbook_run_id, constants.RESULT_FAILURE
        )

    async def polling_loop(self):
        last_output = ""
        if self.id is None:
            return self.mark_as_failed("This host is not known by Satellite")
        while True:
            response = await self.poll_with_retries()
            if response["error"]:
                break
            body = response["body"]
            if body["output"] and (self.run.config.text_updates or body["complete"]):
                last_output = "".join(chunk["output"] for chunk in body["output"])
                if self.since is not None:
                    self.since = body["output"][-1]["timestamp"]
                self.run.queue.playbook_run_update(
                    self.name, self.run.playbook_run_id, last_output, self.sequence
                )
                self.sequence += 1
            if body["complete"]:
                result = constants.RESULT_FAILURE
                if last_output.endswith("Exit status: 0"):
                    result = constants.RESULT_SUCCESS
                elif self.run.cancelled:
                    result = constants.RESULT_CANCEL
                self.run.queue.playbook_run_finished(
                    self.name, self.run.playbook_run_id, result
                )
                break

    async def poll_with_retries(self):
        retry = 0
        while retry < 5:
            await asyncio.sleep(self.run.config.text_update_interval)
            response = await self.run.satellite_api.output(
                self.run.job_invocation_id, self.id, self.since
            )
            if response["error"] is None:
                return response
            retry += 1
        self.mark_as_failed(response["error"])
        return dict(error=True)


class Run:
    def __init__(
        self,
        queue,
        remediation_id,
        playbook_run_id,
        account,
        hosts,
        playbook,
        config,
        satellite_api,
        logger,
    ):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.playbook = playbook
        self.config = Config.from_raw(Config.validate_input(config, logger))

        unsafe_hostnames = [name for name in hosts if "," in name]
        for name in unsafe_hostnames:
            logger.warning(f"Hostname '{name}' contains a comma, skipping")
            Host(self, None, name).mark_as_failed("Hostname contains a comma, skipping")

        self.hosts = [
            Host(self, None, name) for name in hosts if name not in unsafe_hostnames
        ]
        self.satellite_api = satellite_api
        self.logger = logger
        self.job_invocation_id = None
        self.cancelled = False

    @classmethod
    def from_raw(cls, queue, raw, satellite_api, logger):
        return cls(
            queue,
            raw["remediation_id"],
            raw["playbook_run_id"],
            raw["account"],
            raw["hosts"],
            raw["playbook"],
            raw["config"],
            satellite_api,
            logger,
        )

    async def start(self):
        await self.satellite_api.init_session()
        try:
            if not await run_monitor.register(self):
                self.logger.error(
                    f"Playbook run {self.playbook_run_id} already known, skipping."
                )
                return
            response = await self.satellite_api.trigger(
                {"playbook": self.playbook}, [host.name for host in self.hosts]
            )
            self.queue.ack(self.playbook_run_id)
            if response["error"]:
                self.abort(response["error"])
            else:
                self.job_invocation_id = response["body"]["id"]
                self.logger.info(
                    f"Playbook run {self.playbook_run_id} running as job invocation {self.job_invocation_id}"
                )
                self.update_hosts(response["body"]["targeting"]["hosts"])
                await asyncio.gather(*[host.polling_loop() for host in self.hosts])
            await run_monitor.done(self)
            self.logger.info(f"Playbook run {self.playbook_run_id} done")
        finally:
            await self.satellite_api.close_session()

    def update_hosts(self, hosts):
        host_map = {host.name: host for host in self.hosts}
        for host in hosts:
            host_map[host["name"]].id = host["id"]

    def abort(self, error):
        error = str(error)
        self.logger.error(
            f"Playbook run {self.playbook_run_id} encountered error `{error}`, aborting."
        )
        for host in self.hosts:
            host.mark_as_failed(error)


async def cancel_run(satellite_api, run_id, queue, logger):
    logger.info(f"Cancelling playbook run {run_id}")
    run = await run_monitor.get(run_id)
    status = None
    if run is True:
        logger.info(f"Playbook run {run_id} is already finished")
        status = constants.CANCEL_RESULT_FINISHED
    elif run is None:
        logger.info(f"Playbook run {run_id} is not known by receptor")
        status = constants.CANCEL_RESULT_FAILURE
    else:
        await satellite_api.init_session()
        response = await satellite_api.cancel(run.job_invocation_id)
        run.cancelled = True
        await satellite_api.close_session()
        if response["status"] == 422:
            status = constants.CANCEL_RESULT_FINISHED
        elif response["status"] == 200:
            status = constants.CANCEL_RESULT_CANCELLING
        else:
            status = constants.CANCEL_RESULT_FAILURE
    queue.playbook_run_cancel_ack(run_id, status)


def run(coroutine):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(coroutine)


@receptor_export
def execute(message, config, queue):
    logger = configure_logger()
    queue = ResponseQueue(queue)
    payload = json.loads(message.raw_payload)
    satellite_api = SatelliteAPI.from_plugin_config(config["plugin_config"])
    run(Run.from_raw(queue, payload, config, satellite_api, logger).start())


@receptor_export
def cancel(message, config, queue):
    logger = configure_logger()
    queue = ResponseQueue(queue)
    satellite_api = SatelliteAPI.from_plugin_config(config)
    payload = json.loads(message.raw_payload)
    run(cancel_run(satellite_api, payload.get("playbook_run_id"), queue, logger))


@receptor_export
def health_check(message, config, queue):
    logger = configure_logger()
    try:
        payload = json.loads(message.raw_payload)
    except json.JSONDecodeError:
        logger.exception("Invalid JSON format for payload.")
        raise

    try:
        api = SatelliteAPI.from_plugin_config(config)
    except KeyError:
        result = dict(
            result=HEALTH_CHECK_ERROR, **HEALTH_STATUS_RESULTS[HEALTH_CHECK_ERROR]
        )
    else:
        result = run(api.health_check(payload.get("satellite_instance_id", "")))
    queue.put(result)
