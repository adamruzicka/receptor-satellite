from receptor_satellite.response.constants import RESULT_SUCCESS


def playbook_run_completed(
    playbook_run_id,
    status,  # One of RESULT_{SUCCESS,FAILURE,CANCEL}
    connection_code=0,  # 0 (success) || 1 (error) || null (n case job was cancelled)
    connection_error=None,  # “Satellite unreachable” || null (n case job was cancelled),
    infrastructure_code=0,  # 0 (success) || 1 (error) || null (in case satellite connection code is 1) || null (n case job was cancelled)
    infrastructure_error=None,  # “Capsule is down” || null (n case job was cancelled)
):

    return {
        "version": 2,
        "type": "playbook_run_completed",
        "playbook_run_id": playbook_run_id,
        "status": status,
        "satellite_connection_code": connection_code,
        "satellite_connection_error": connection_error,
        "satellite_infrastructure_code": infrastructure_code,
        "satellite_infrastructure_error": infrastructure_error,
    }


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
