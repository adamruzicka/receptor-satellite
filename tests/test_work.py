import json
import logging
import os
import pytest
import queue

from receptor_satellite import worker
from constants import UUID


logger = logging.getLogger(__name__)


class FakeInnerEnvelope:
    raw_payload = None


@pytest.mark.skipif(
    not os.environ.get("SATELLITE_URL", None),
    reason="No configured Satellite"
)
def test_health_check_task():
    q = queue.Queue()
    message = FakeInnerEnvelope()
    message.raw_payload = json.dumps(dict(foreman_uuid=UUID))
    config = dict(
        username=os.environ.get("SATELLITE_USERNAME"),
        password=os.environ.get("SATELLITE_PASSWORD"),
        url=os.environ.get("SATELLITE_URL"),
        ca_cert=None,
        validate_cert=False,
    )
    worker.health_check(message, config, q)
    result = q.get()
    logger.info(result)
