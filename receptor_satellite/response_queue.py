class ResponseQueue:

    def __init__(self, queue):
        self.queue = queue

    def ack(self, playbook_run_id):
        payload = {
            'type': 'playbook_run_ack',
            'playbook_run_id': playbook_run_id
        }
        return self.queue.put(payload)

    def playbook_run_update(self, host, playbook_run_id, output, sequence):
        payload = {
            'type': 'playbook_run_update',
            'playbook_run_id': playbook_run_id,
            'sequence': sequence,
            'host': host,
            'console': output
        }
        return self.queue.put(payload)

    def playbook_run_finished(self, host, playbook_run_id, success=True):
        payload = {
            'type': 'playbook_run_finished',
            'playbook_run_id': playbook_run_id,
            'host': host,
            'status': 'success' if success else 'failure'
        }
        return self.queue.put(payload)

