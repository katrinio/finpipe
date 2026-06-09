class FakeSendCall:
    def __init__(self, response: dict | Exception) -> None:
        self.response = response
        self.payload = None

    def execute(self) -> dict:
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class FakeMessages:
    def __init__(self, response: dict | Exception) -> None:
        self.response = response
        self.sent_bodies: list[dict] = []

    def send(self, userId: str, body: dict) -> FakeSendCall:
        self.sent_bodies.append(body)
        return FakeSendCall(self.response)


class FakeUsers:
    def __init__(self, response: dict | Exception) -> None:
        self.messages_client = FakeMessages(response)

    def messages(self) -> FakeMessages:
        return self.messages_client


class FakeService:
    def __init__(self, response: dict | Exception) -> None:
        self.users_client = FakeUsers(response)

    def users(self) -> FakeUsers:
        return self.users_client
