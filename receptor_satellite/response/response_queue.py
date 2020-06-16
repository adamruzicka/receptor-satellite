import receptor_satellite.response.constants as constants
import receptor_satellite.response.messages as messages


class ResponseQueue:
    def __init__(self, queue):
        self.queue = queue

    def ack(self, playbook_run_id):
        self.queue.put(messages.ack(playbook_run_id))

    def playbook_run_update(self, host, playbook_run_id, output, sequence):
        self.queue.put(
            messages.playbook_run_update(host, playbook_run_id, output, sequence)
        )

    def playbook_run_finished(
        self, host, playbook_run_id, result=constants.RESULT_SUCCESS
    ):
        self.queue.put(messages.playbook_run_finished(host, playbook_run_id, result))

    def playbook_run_completed(
        self, playbook_run_id, status, connection_error=None, infrastructure_error=None
    ):
        connection_code = 0
        infrastructure_code = 0
        if connection_error:
            connection_code = 1
            infrastructure_code = None
        elif infrastructure_error:
            infrastructure_code = 1
        if status == constants.RESULT_CANCEL:
            connection_code = None
            infrastructure_code = None

        self.queue.put(
            messages.playbook_run_completed(
                playbook_run_id,
                status,
                connection_code,
                connection_error,
                infrastructure_code,
                infrastructure_error,
            )
        )

    def playbook_run_cancel_ack(self, playbook_run_id, status):
        self.queue.put(messages.playbook_run_cancel_ack(playbook_run_id, status))
