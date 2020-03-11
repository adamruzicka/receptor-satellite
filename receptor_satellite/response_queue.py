class ResponseQueue:
    def __init__(self, queue):
        self.queue = queue

    def ack(self, playbook_run_id):
        self.queue.put({"type": "playbook_run_ack", "playbook_run_id": playbook_run_id})

    def playbook_run_update(self, host, playbook_run_id, output, sequence):
        self.queue.put(
            {
                "type": "playbook_run_update",
                "playbook_run_id": playbook_run_id,
                "sequence": sequence,
                "host": host,
                "console": output,
            }
        )

    def playbook_run_finished(self, host, playbook_run_id, success=True):
        self.queue.put(
            {
                "type": "playbook_run_finished",
                "playbook_run_id": playbook_run_id,
                "host": host,
                "status": "success" if success else "failure",
            }
        )

    def playbook_run_cancel_ack(self, playbook_run_id, status):
        self.queue.put(
            {
                "type": "playbook_run_cancel_ack",
                "playbook_run_id": playbook_run_id,
                "status": status,
            }
        )
