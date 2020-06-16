import pytest

from receptor_satellite.response.response_queue import ResponseQueue
import receptor_satellite.response.constants as constants
import receptor_satellite.response.messages as messages
from fake_queue import FakeQueue

PLAYBOOK_RUN_COMPLETED_TEST_CASES = [
    (
        # ((run_id, result, connection_error, infrastructure_error), expectation)
        ("some-uuid", constants.RESULT_SUCCESS, None, None),
        messages.playbook_run_completed("some-uuid", constants.RESULT_SUCCESS),
    ),
    (
        ("some-uuid", constants.RESULT_FAILURE, None, None),
        messages.playbook_run_completed("some-uuid", constants.RESULT_FAILURE,),
    ),
    (
        ("some-uuid", constants.RESULT_CANCEL, None, None),
        messages.playbook_run_completed(
            "some-uuid",
            constants.RESULT_CANCEL,
            infrastructure_code=None,
            connection_code=None,
        ),
    ),
    (
        ("some-uuid", constants.RESULT_FAILURE, "Satellite unreachable", None),
        messages.playbook_run_completed(
            "some-uuid",
            constants.RESULT_FAILURE,
            infrastructure_code=None,
            connection_code=1,
            connection_error="Satellite unreachable",
        ),
    ),
    (
        ("some-uuid", constants.RESULT_FAILURE, None, "Capsule is down"),
        messages.playbook_run_completed(
            "some-uuid",
            constants.RESULT_FAILURE,
            connection_code=0,
            infrastructure_code=1,
            infrastructure_error="Capsule is down",
        ),
    ),
]


@pytest.fixture(scope="module", params=PLAYBOOK_RUN_COMPLETED_TEST_CASES)
def playbook_run_completed_scenario(request):
    yield request.param


def test_playbook_run_completed(playbook_run_completed_scenario):
    params, expectation = playbook_run_completed_scenario
    uuid, result, connection_error, infrastructure_error = params
    fake_queue = FakeQueue()
    queue = ResponseQueue(fake_queue)

    queue.playbook_run_completed(uuid, result, connection_error, infrastructure_error)
    print(expectation)
    assert fake_queue.messages == [expectation]
