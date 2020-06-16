from receptor_satellite.response.constants import RESULT_SUCCESS


def playbook_run_cancel_ack(self, playbook_run_id, status):
    return {
        "type": "playbook_run_cancel_ack",
        "playbook_run_id": playbook_run_id,
        "status": status,
    }


def playbook_run_finished(host, playbook_run_id, result=RESULT_SUCCESS):
    return {
        "type": "playbook_run_finished",
        "playbook_run_id": playbook_run_id,
        "host": host,
        "status": result,
    }


def playbook_run_update(host, playbook_run_id, output, sequence):
    return {
        "type": "playbook_run_update",
        "playbook_run_id": playbook_run_id,
        "sequence": sequence,
        "host": host,
        "console": output,
    }


def ack(playbook_run_id):
    return {"type": "playbook_run_ack", "playbook_run_id": playbook_run_id}
