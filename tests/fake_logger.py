class FakeLogger:
    def __init__(self):
        self.messages = []

    def log(self, level, message):
        self.messages.append({"level": level, "message": message})

    def by_level(self, level):
        return [log["message"] for log in self.messages if log["level"] == level]

    def warning(self, message):
        self.log("warning", message)
        return self

    def error(self, message):
        self.log("error", message)
        return self

    def info(self, message):
        self.log("info", message)
        return self

    def errors(self):
        return self.by_level("error")

    def infos(self):
        return self.by_level("info")

    def warnings(self):
        return self.by_level("warning")
