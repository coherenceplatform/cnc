import os
from inspect import currentframe
from rich import print


def get_logger(name="root"):
    return Logger(name)


class Logger:
    def __init__(self, name):
        self.name = name

    def debug(self, msg):
        debug = bool(os.environ.get("CNC_DEBUG", True))
        if debug:
            print(
                f"[green]DEBUG ({self.name}:{currentframe().f_back.f_lineno})"
                f"[/ green] {msg}"
            )

    def info(self, msg):
        print(
            f"[blue]INFO ({self.name}:{currentframe().f_back.f_lineno})"
            f"[/ blue] {msg}"
        )

    def warning(self, msg):
        print(
            f"[yellow]WARNING ({self.name}:{currentframe().f_back.f_lineno})"
            f"[/ yellow] {msg}"
        )

    def error(self, msg):
        print(
            f"[red]ERROR ({self.name}:{currentframe().f_back.f_lineno})"
            f"[/ red] {msg}"
        )
