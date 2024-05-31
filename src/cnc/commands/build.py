import typer
import time
from typing import List
from typing_extensions import Annotated

from cnc.models import BuildStageManager
from .telemetry import send_event

from cnc.logger import get_logger

log = get_logger(__name__)


app = typer.Typer()


@app.command()
def perform(
    ctx: typer.Context,
    environment_name: str,
    service_tags: List[str] = typer.Option(
        [],
        "--service-tag",
        "-t",
        help="Set the tag to use for this service with svc_name=tag, default is 'int(time.time())'. If any provided, only builds provided services and will build all services if empty",
    ),
    default_tag: Annotated[
        str,
        typer.Option(
            "-d", "--default-tag", envvar="CNC_DEFAULT_TAG", help="CNC default tag"
        ),
    ] = None,
    collection_name: str = "",
    cleanup: bool = True,
    debug: bool = False,
    generate: bool = True,
    webhook_url: str = typer.Option(
        None,
        "--webhook-url",
        help="Webhook URL for sending build notifications",
    ),
    webhook_token: str = typer.Option(
        None,
        "--webhook-token",
        help="Webhook token for authentication",
    ),
):
    """Build containers for config-defined services"""
    start_time = time.time()
    send_event("build.perform")
    collection = ctx.obj.application.collection_by_name(collection_name)
    if not collection:
        log.error(f"No collection found for: {collection_name}")
        raise typer.Exit(code=1)

    environment = collection.environment_by_name(environment_name)
    if not environment:
        log.error(f"No environment found for: {environment_name}")
        raise typer.Exit(code=1)

    builder = BuildStageManager(
        environment,
        service_tags=service_tags,
        default_tag=default_tag,
        webhook_url=webhook_url,
        webhook_token=webhook_token,
    )
    cmd_exit_code = builder.perform(
        should_cleanup=cleanup,
        should_regenerate_config=generate,
        debug=debug,
    )

    log.debug(
        f"All set building for {builder.config_files_path} in "
        f"{int(start_time - time.time())} seconds"
    )
    raise typer.Exit(code=cmd_exit_code)
