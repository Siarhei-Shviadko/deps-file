from collections import namedtuple

__all__ = ["FakeCommandProducer", "Command"]

Command = namedtuple("Command", ("channel", "command", "reply_to"))


class FakeCommandProducer:
    def __init__(self) -> None:
        self.sent_commands: list[Command] = []

    @property
    def last_command(self) -> list[Command]:
        return self.sent_commands

    def send(self, channel: str, command: Command, reply_to: str, **kwargs) -> None:
        self.sent_commands.append(Command(channel=channel, command=command, reply_to=reply_to))

    def clear(self) -> None:
        self.sent_commands.clear()
