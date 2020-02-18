import asyncio
import logging
import pytest

from receptor_satellite.satellite_api import SatelliteAPI
from constants import *

logger = logging.getLogger(__name__)


# error code, fifi_status, foreman_uuid, {url: response}
TEST_CASES = [
    # Satellite not contactable
    (
        1, 
        False, 
        None, 
        {UUID_URL: dict(error="Missing Satellite", status=-1, body="{}")}
    ),
    # Satellite throwing errors
    (
        2,
        False,
        None,
        {UUID_URL: dict(error="Broken Satellite", status=500, body="<html></html>")},
    ),
    # Satellite UUID unknown
    (
        3, 
        False, 
        UUID, 
        {UUID_URL: dict(error=None, status=200, body=MISSING_UUID_RESPONSE_BODY)}
    ),
    # Satellite UUID mismatch
    (
        4, 
        False, 
        BAD_UUID, 
        {UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY)}
    ),
    # No Smart Proxies
    (
        5,
        False,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(error=None, status=200, body=NO_CAPSULES_STATUSES_RESPONSE_BODY)
        }
    ),
    # No Ansible in Smart Proxies
    (
        6,
        False,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(error=None, status=200, body=NO_ANSIBLE_STATUSES_RESPONSE_BODY)
        }
    ),
    # Smart Proxies down
    (
        7,
        False,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(error=None, status=200, body=DOWN_CAPSULE_STATUSES_RESPONSE_BODY)
        }
    ),
    # All systems go
    (
        0,
        True,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(error=None, status=200, body=STATUSES_RESPONSE_BODY)
        }
    )
]


class FakeSatelliteAPI(SatelliteAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_map = {}

    async def request(self, method, url, extra_data):
        to_return = self.response_map.get(
            url, dict(error="Not found", body="{}", status=404)
        )
        logger.debug(f'Request for {url} -> {to_return}')
        return to_return


@pytest.fixture(scope='module', params=TEST_CASES)
def scenario(request):
    status_code, fifi_status, uuid, response_map = request.param
    api = FakeSatelliteAPI("username", "password", "http://localhost", None)
    api.response_map = response_map
    yield (status_code, fifi_status, uuid, api)


def test_health_check(scenario):
    status_code, fifi_status, uuid, api = scenario
    response = asyncio.run(api.health_check(uuid))
    assert response['code'] == status_code
    assert response['fifi_status'] == fifi_status
    if response['code'] in [0, 5, 6, 7]:
        assert response['result'] == 'ok'
    else:
        assert response['result'] == 'error'
