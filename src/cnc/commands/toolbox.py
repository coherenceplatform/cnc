from typing import List
import typer

from .telemetry import send_event

from cnc.logger import get_logger

log = get_logger(__name__)


app = typer.Typer()


@app.callback()
def add_common(
    ctx: typer.Context,
    collection_name: str = typer.Option(
        default="", envvar="CNC_COLLECTION_NAME", help="Collection name"
    ),
):
    """Common Entry Point for Toolbox"""
    print(ctx.obj)
    collection = ctx.obj.application.collection_by_name(collection_name)
    if not collection:
        log.error(
            f"No collection found for: {collection_name} | (configured "
            f"collections are: {[c.name for c in ctx.obj.application.collections]})"
        )
        raise typer.Exit(code=1)

    ctx.obj.collection = collection


@app.command()
def start(
    ctx: typer.Context,
    environment_name: str,
    service_name: str = "",
    tag: str = "latest",
):
    send_event("toolbox.start")
    collection = ctx.obj.collection

    environment = collection.environment_by_name(environment_name)
    if not environment:
        log.error(f"No environment found for: {environment_name}")
        raise typer.Exit(code=1)

    if service_name:
        service = environment.service_by_name(service_name)
        if not service:
            log.error(f"No service found for: {service_name}")
            raise typer.Exit(code=1)
    else:
        # If no service specified, default to first backend service
        if not environment.backend_services:
            log.error(f"No backend service found for environment: {environment_name}")
            raise typer.Exit(code=1)

        service = environment.backend_services[0]

    toolbox = service.toolbox_manager(environment_tag=tag)
    toolbox.start()

    log.debug(f"Toolbox stopped for {toolbox.config_files_path}")
    raise typer.Exit()


@app.command()
def run(
    ctx: typer.Context,
    environment_name: str,
    command: List[str],
    service_name: str = "",
    tag: str = "latest",
):
    send_event("toolbox.run")
    collection = ctx.obj.collection

    environment = collection.environment_by_name(environment_name)
    if not environment:
        log.error(f"No environment found for: {environment_name}")
        raise typer.Exit(code=1)

    if service_name:
        service = environment.service_by_name(service_name)
        if not service:
            log.error(f"No service found for: {service_name}")
            raise typer.Exit(code=1)
    else:
        # If no service specified, default to first backend service
        if not environment.backend_services:
            log.error(f"No backend service found for environment: {environment_name}")
            raise typer.Exit(code=1)

        service = environment.backend_services[0]

    toolbox = service.toolbox_manager(environment_tag=tag)
    cmd_exit_code = toolbox.run(command)

    log.debug(f"Toolbox stopped for {toolbox.config_files_path}")
    raise typer.Exit(code=cmd_exit_code)
