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

    def playbook_run_cancel_ack(self, playbook_run_id, status):
        self.queue.put(messages.playbook_run_cancel_ack(playbook_run_id, status))
