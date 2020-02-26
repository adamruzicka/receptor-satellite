import json
import logging
import os
import pytest
import queue

from receptor_satellite import worker
from receptor_satellite.satellite_api import HEALTH_OK, HEALTH_CHECK_OK


logger = logging.getLogger(__name__)


class FakeInnerEnvelope:
    raw_payload = None


@pytest.mark.skipif(
    not os.environ.get("SATELLITE_URL", None), reason="No configured Satellite"
)
def test_health_check_task():
    q = queue.Queue()
    message = FakeInnerEnvelope()
    message.raw_payload = json.dumps(
        dict(satellite_instance_id=os.environ.get("SATELLITE_INSTANCE_ID"))
    )
    config = dict(
        username=os.environ.get("SATELLITE_USERNAME"),
        password=os.environ.get("SATELLITE_PASSWORD"),
        url=os.environ.get("SATELLITE_URL"),
        ca_cert=None,
        validate_cert="0",
    )
    worker.health_check(message, config, q)
    result = q.get()
    logger.info(result)
    assert result["result"] == HEALTH_CHECK_OK
    assert result["code"] == HEALTH_OK
