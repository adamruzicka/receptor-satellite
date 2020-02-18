import asyncio
import json
import logging

from .satellite_api import SatelliteAPI
from .response_queue import ResponseQueue
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


class Config:
    def __init__(
        self, text_updates=False, text_update_interval=5000, text_update_full=True
    ):
        self.text_updates = text_updates
        self.text_update_interval = text_update_interval
        self.text_update_full = text_update_full

    @classmethod
    def from_raw(cls, raw={}):
        return cls(
            raw["text_updates"], raw["text_update_interval"], raw["text_update_full"]
        )


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
        queue.playbook_run_finished(self.name, playbook_run_id, False)

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
                self.run.queue.playbook_run_finished(
                    self.name,
                    self.run.playbook_run_id,
                    last_output.endswith("Exit status: 0"),
                )
                break

    async def poll_with_retries(self):
        retry = 0
        while retry < 5:
            await asyncio.sleep(self.run.config.text_update_interval / 1000)
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
        plugin_config,
        logger,
    ):
        self.queue = queue
        self.remedation_id = remediation_id
        self.playbook_run_id = playbook_run_id
        self.account = account
        self.playbook = playbook
        self.config = Config.from_raw(config)
        self.hosts = [Host(self, None, name) for name in hosts]
        self.satellite_api = SatelliteAPI.from_plugin_config(plugin_config)
        self.logger = logger

    @classmethod
    def from_raw(cls, queue, raw, plugin_config, logger):
        return cls(
            queue,
            raw["remediation_id"],
            raw["playbook_run_id"],
            raw["account"],
            raw["hosts"],
            raw["playbook"],
            raw["config"],
            plugin_config,
            logger,
        )

    async def start(self):
        await self.satellite_api.init_session()
        if not await run_monitor.register(self):
            self.logger.info(
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
                f"Playbook run {self.playbook_run_id} running as job invocation {self.job_invocatino_id}"
            )
            self.update_hosts(response["body"]["targeting"]["hosts"])
            await asyncio.gather(*[host.polling_loop() for host in self.hosts])
        await asyncio.gather(run_monitor.done(self), self.satellite_api.close_session())
        self.logger.info(f"Playbook run {self.playbook_run_id} done")

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


@receptor_export
def execute(message, config, queue):
    logger = configure_logger()
    queue = ResponseQueue(queue)
    payload = json.loads(message.raw_payload)
    asyncio.run(Run.from_raw(queue, payload, config, logger).start())


@receptor_export
def health_check(message, config, queue):
    logger = configure_logger()
    try:
        payload = json.loads(message.raw_payload)
    except json.JSONDecodeError:
        logger.exeception('Invalid JSON format for payload.')
        raise
    
    api = SatelliteAPI.from_plugin_config(config)
    result = asyncio.run(api.health_check(payload.get('foreman_uuid', '')))
    queue.put(result)
