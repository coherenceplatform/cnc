import typer
from IPython import embed
from cnc.models import (
    # Environment,
    # EnvironmentVariable,
    # AppConfig,
    # EnvironmentCollection,
    Application,
)
from .telemetry import send_event

from cnc.logger import get_logger

log = get_logger(__name__)
app = typer.Typer()


def get_app():
    app = Application.from_environments_yml("environments.yml")
    return app


@app.callback(invoke_without_command=True)
@app.command()
def start(ctx: typer.Context):
    send_event("shell.start")
    local_vars = {
        "get_app": get_app,
        "parse_yml": get_app,
    }
    embed(user_ns=local_vars, colors="neutral")
    raise typer.Exit()
