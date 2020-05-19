from fake_logger import FakeLogger

import asyncio
import pytest


async def _sleep_override(interval):
    pass


asyncio.sleep = _sleep_override

from receptor_satellite.worker import Config, Host, Run, ResponseQueue  # noqa: E402
from receptor_satellite.response_queue import ResponseQueue  # noqa: E402


class FakeQueue:
    def __init__(self):
        self.messages = []

    def put(self, message):
        self.messages.append(message)


def test_hostname_sanity():
    hosts = ["good", "fine", "not,really,good", "ok"]
    logger = FakeLogger()
    fake_queue = FakeQueue()
    playbook_id = "play_id"

    run = Run(
        ResponseQueue(fake_queue),
        "rem_id",
        playbook_id,
        "acc_num",
        hosts,
        "playbook",
        {},
        None,  # No need for SatelliteAPI in this test
        logger,
    )
    assert logger.warnings == ["Hostname 'not,really,good' contains a comma, skipping"]
    assert fake_queue.messages == [
        {
            "type": "playbook_run_update",
            "playbook_run_id": playbook_id,
            "sequence": 0,
            "host": "not,really,good",
            "console": "Hostname contains a comma, skipping",
        },
        {
            "type": "playbook_run_finished",
            "playbook_run_id": playbook_id,
            "host": "not,really,good",
            "status": "failure",
        },
    ]
    assert list(map(lambda h: h.name, run.hosts)) == ["good", "fine", "ok"]


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


# (host_id, output_value, result, api_requests, queue_messages
POLL_WITH_RETRIES_TEST_CASES = [
    # Polling loop does not loop if there is no error when talking to
    # the API
    (
        1,
        {"error": None, "key": "value"},
        {"error": None, "key": "value"},
        [("output", (None, 1, None))],
        [],
    ),
    # Polling loop polls 5 times if response contains an error and
    # marks the host as failed afterwards
    (
        1,
        {"error": "controlled failure"},
        {"error": True},
        [
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
        ],
        [
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
    host_id, output_value, result, api_requests, queue_messages = request.param
    queue, logger, satellite_api, run = base_scenario
    host = Host(run, host_id, "host1")

    yield (queue, host, output_value, result, api_requests, queue_messages)


@pytest.mark.asyncio
async def test_poll_with_retries(poll_with_retries_scenario):
    (
        queue,
        host,
        output_value,
        expected_result,
        api_requests,
        queue_messages,
    ) = poll_with_retries_scenario
    satellite_api = host.run.satellite_api
    satellite_api.real_output = lambda j, h, s: output_value

    result = await host.poll_with_retries()

    assert result == expected_result
    assert satellite_api.requests == api_requests
    assert queue.messages == queue_messages


# (host_id, run_cancelled, api_output, expected_result, api_requests, queue_messages)
POLLING_LOOP_TEST_CASES = [
    # If the host doesn't have an ID, it is assumed to be not known by
    # Satellite and is marked as failed
    (
        None,
        False,
        None,
        None,
        [],
        [
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
    (
        1,
        False,
        {"error": "controlled failure"},
        None,
        [
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
            ("output", (None, 1, None)),
        ],
        [
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
    (
        1,
        False,
        {
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 0"}]},
        },
        None,
        [("output", (None, 1, None))],
        [
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
    (
        1,
        True,
        {
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 0"}]},
        },
        None,
        [("output", (None, 1, None))],
        [
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
    (
        1,
        False,
        {
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 123"}]},
        },
        None,
        [("output", (None, 1, None))],
        [
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
    (
        1,
        True,
        {
            "error": None,
            "body": {"complete": True, "output": [{"output": "Exit status: 123"}]},
        },
        None,
        [("output", (None, 1, None))],
        [
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
    (
        host_id,
        run_cancelled,
        output_value,
        result,
        api_requests,
        queue_messages,
    ) = request.param
    queue, logger, satellite_api, run = base_scenario
    run.cancelled = run_cancelled
    host = Host(run, host_id, "host1")

    yield (queue, host, output_value, result, api_requests, queue_messages)


@pytest.mark.asyncio
async def test_polling_loop(polling_loop_scenario):
    (
        queue,
        host,
        output_value,
        expected_result,
        api_requests,
        queue_messages,
    ) = polling_loop_scenario
    satellite_api = host.run.satellite_api
    satellite_api.real_output = lambda j, h, s: output_value
    result = await host.polling_loop()
    assert result == expected_result
    assert satellite_api.requests == api_requests
    assert queue.messages == queue_messages
