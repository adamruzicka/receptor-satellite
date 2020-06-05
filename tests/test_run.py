import asyncio
import pytest


async def _sleep_override(interval):
    pass


asyncio.sleep = _sleep_override

from receptor_satellite.worker import Config, Host, Run  # noqa: E402
from receptor_satellite.response_queue import ResponseQueue  # noqa: E402


class FakeQueue:
    def __init__(self):
        self.messages = []

    def put(self, message):
        self.messages.append(message)


class FakeLogger:
    def __init__(self):
        self.errors = []

    def error(self, message):
        self.errors.append(message)


class FakeSatelliteAPI:
    def __init__(self):
        self.requests = []

    def record_request(self, request_type, data):
        self.requests.append((request_type, data))

    def real_output(self, job_id, host_id, since):
        return {"error": None}

    async def output(self, job_id, host_id, since):
        self.record_request("output", (job_id, host_id, since))
        return self.real_output(job_id, host_id, since)


@pytest.fixture
def base_scenario(request):
    queue = FakeQueue()
    logger = FakeLogger()
    satellite_api = FakeSatelliteAPI()
    run = Run(
        ResponseQueue(queue),
        "rem_id",
        "play_id",
        "account_no",
        ["host1"],
        "playbook",
        Config(),
        satellite_api,
        logger,
    )
    yield (queue, logger, satellite_api, run)


def test_mark_as_failed(base_scenario):
    queue, logger, satellite_api, run = base_scenario
    host = Host(run, None, "host1")
    host.mark_as_failed("controlled failure")

    assert queue.messages == [
        {
            "type": "playbook_run_update",
            "playbook_run_id": "play_id",
            "sequence": 0,
            "host": host.name,
            "console": "controlled failure",
        },
        {
            "type": "playbook_run_finished",
            "playbook_run_id": "play_id",
            "host": host.name,
            "status": ResponseQueue.RESULT_FAILURE,
        },
    ]


class PollWithRetriesTestCase:
    def __init__(
        self,
        host_id=1,
        api_output=None,
        result=None,
        api_requests=[],
        queue_messages=[],
    ):
        self.host_id = host_id
        self.api_output = api_output
        self.result = result
        self.api_requests = api_requests
        self.queue_messages = queue_messages


POLL_WITH_RETRIES_TEST_CASES = [
    # Polling loop does not loop if there is no error when talking to
    # the API
    PollWithRetriesTestCase(
        result={"error": None, "key": "value"},
        api_output={"error": None, "key": "value"},
        api_requests=[("output", (None, 1, None))],
    ),
    PollWithRetriesTestCase(
        result={"error": True},
        api_output={"error": "controlled failure"},
        api_requests=[("output", (None, 1, None)) for _x in range(5)],
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "controlled failure",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_FAILURE,
            },
        ],
    ),
]


@pytest.fixture(params=POLL_WITH_RETRIES_TEST_CASES)
def poll_with_retries_scenario(request, base_scenario):
    # host_id, output_value, result, api_requests, queue_messages = request.param
    param = request.param
    queue, logger, satellite_api, run = base_scenario
    host = Host(run, param.host_id, "host1")

    yield (queue, host, param)


@pytest.mark.asyncio
async def test_poll_with_retries(poll_with_retries_scenario):
    (queue, host, param,) = poll_with_retries_scenario
    satellite_api = host.run.satellite_api
    satellite_api.real_output = lambda j, h, s: param.api_output

    result = await host.poll_with_retries()

    assert result == param.result
    assert satellite_api.requests == param.api_requests
    assert queue.messages == param.queue_messages


class PollingLoopTestCase(PollWithRetriesTestCase):
    def __init__(self, cancelled=False, **kwargs):
        super().__init__(**kwargs)
        self.cancelled = cancelled


POLLING_LOOP_TEST_CASES = [
    # If the host doesn't have an ID, it is assumed to be not known by
    # Satellite and is marked as failed
    PollingLoopTestCase(
        host_id=None,
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "This host is not known by Satellite",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_FAILURE,
            },
        ],
    ),
    # If the polling loop receives an error from the API, it marks the
    # host as failed
    PollingLoopTestCase(
        api_output={"error": "controlled failure"},
        api_requests=[("output", (None, 1, None)) for _x in range(5)],
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "controlled failure",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_FAILURE,
            },
        ],
    ),
    # If the last output from the API ends with Exit status: 0, mark
    # the run on the host as success
    PollingLoopTestCase(
        api_output={
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 0"}]},
        },
        api_requests=[("output", (None, 1, None))],
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "Exit status: 0",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_SUCCESS,
            },
        ],
    ),
    # If the run was cancelled, but the host managed to finish
    # successfully, mark it as success
    PollingLoopTestCase(
        cancelled=True,
        api_output={
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 0"}]},
        },
        api_requests=[("output", (None, 1, None))],
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "Exit status: 0",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_SUCCESS,
            },
        ],
    ),
    # If the host failed, mark it as failed
    PollingLoopTestCase(
        api_output={
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 123"}]},
        },
        api_requests=[("output", (None, 1, None))],
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "Exit status: 123",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_FAILURE,
            },
        ],
    ),
    # If the run was cancelled and the run on the host failed, mark it
    # as cancelled
    PollingLoopTestCase(
        cancelled=True,
        api_output={
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 123"}]},
        },
        api_requests=[("output", (None, 1, None))],
        queue_messages=[
            {
                "type": "playbook_run_update",
                "playbook_run_id": "play_id",
                "sequence": 0,
                "host": "host1",
                "console": "Exit status: 123",
            },
            {
                "type": "playbook_run_finished",
                "playbook_run_id": "play_id",
                "host": "host1",
                "status": ResponseQueue.RESULT_CANCEL,
            },
        ],
    ),
]


@pytest.fixture(params=POLLING_LOOP_TEST_CASES)
def polling_loop_scenario(request, base_scenario):
    queue, logger, satellite_api, run = base_scenario
    run.cancelled = request.param.cancelled
    host = Host(run, request.param.host_id, "host1")

    yield (queue, host, request.param)


@pytest.mark.asyncio
async def test_polling_loop(polling_loop_scenario):
    (queue, host, param,) = polling_loop_scenario
    satellite_api = host.run.satellite_api
    satellite_api.real_output = lambda j, h, s: param.api_output
    result = await host.polling_loop()
    assert result == param.result
    assert satellite_api.requests == param.api_requests
    assert queue.messages == param.queue_messages
