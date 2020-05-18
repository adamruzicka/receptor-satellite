from receptor_satellite.worker import Run, ResponseQueue
from fake_logger import FakeLogger


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
