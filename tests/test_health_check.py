import asyncio
import logging
import pytest

from receptor_satellite.satellite_api import (
    SatelliteAPI,
    HEALTH_STATUS_RESULTS,
    HEALTH_OK,
    HEALTH_NO_CONNECTION,
    HEALTH_BAD_HTTP_STATUS,
    HEALTH_UUID_UNKNOWN,
    HEALTH_UUID_MISMATCH,
    HEALTH_SP_UNKNOWN,
    HEALTH_SP_NO_ANSIBLE,
    HEALTH_SP_OFFLINE,
)
from constants import *


logger = logging.getLogger(__name__)


# error code, fifi_status, foreman_uuid, {url: response}
TEST_CASES = [
    (
        HEALTH_NO_CONNECTION,
        None,
        {UUID_URL: dict(error="Missing Satellite", status=-1, body="{}")},
    ),
    # Satellite throwing errors
    (
        HEALTH_BAD_HTTP_STATUS,
        None,
        {UUID_URL: dict(error="Broken Satellite", status=500, body="<html></html>")},
    ),
    # Satellite UUID unknown
    (
        HEALTH_UUID_UNKNOWN,
        UUID,
        {UUID_URL: dict(error=None, status=200, body=MISSING_UUID_RESPONSE_BODY)},
    ),
    # Satellite UUID mismatch
    (
        HEALTH_UUID_MISMATCH,
        BAD_UUID,
        {UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY)},
    ),
    # No Smart Proxies
    (
        HEALTH_SP_UNKNOWN,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(
                error=None, status=200, body=NO_CAPSULES_STATUSES_RESPONSE_BODY
            ),
        },
    ),
    # No Ansible in Smart Proxies
    (
        HEALTH_SP_NO_ANSIBLE,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(
                error=None, status=200, body=NO_ANSIBLE_STATUSES_RESPONSE_BODY
            ),
        },
    ),
    # Smart Proxies down
    (
        HEALTH_SP_OFFLINE,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(
                error=None, status=200, body=DOWN_CAPSULE_STATUSES_RESPONSE_BODY
            ),
        },
    ),
    # All systems go
    (
        HEALTH_OK,
        UUID,
        {
            UUID_URL: dict(error=None, status=200, body=UUID_RESPONSE_BODY),
            STATUSES_URL: dict(error=None, status=200, body=STATUSES_RESPONSE_BODY),
        },
    ),
]


class FakeSatelliteAPI(SatelliteAPI):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.response_map = {}

    async def request(self, method, url, extra_data):
        to_return = self.response_map.get(
            url, dict(error="Not found", body="{}", status=404)
        )
        logger.debug(f"Request for {url} -> {to_return}")
        return to_return


@pytest.fixture(scope="module", params=TEST_CASES)
def scenario(request):
    status_code, uuid, response_map = request.param
    api = FakeSatelliteAPI(**PLUGIN_CONFIG)
    api.response_map = response_map
    yield (status_code, uuid, api)


def test_health_check(scenario):
    status_code, uuid, api = scenario
    response = asyncio.run(api.health_check(uuid))
    status_result = HEALTH_STATUS_RESULTS[status_code]
    assert response["code"] == status_code
    assert response["fifi_status"] == status_result["fifi_status"]
    assert response["result"] == status_result["result"]
