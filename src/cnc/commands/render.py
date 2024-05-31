import typer
from cnc.models import ProvisionStageManager, DeployStageManager, BuildStageManager
from .telemetry import send_event

from cnc.logger import get_logger

log = get_logger(__name__)

app = typer.Typer()


@app.callback(invoke_without_command=True)
@app.command()
def render(
    ctx: typer.Context,
    stage: str = "provision",
    extra_context: dict = None,
):
    send_event("render.render")

    manager_map = {
        "build": BuildStageManager,
        "provision": ProvisionStageManager,
        "deploy": DeployStageManager,
    }

    if not manager_map.get("stage"):
        log.error(f"No manager for {stage}")
        raise typer.Exit(code=1)

    # get manager
    # render template with added context

    raise typer.Exit()
