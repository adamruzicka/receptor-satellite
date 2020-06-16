class FakeQueue:
    def __init__(self):
        self.messages = []

    def put(self, message):
        self.messages.append(message)
