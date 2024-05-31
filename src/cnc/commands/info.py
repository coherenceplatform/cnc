import os

from tabulate import tabulate
import typer
import toml

from .telemetry import send_event

from cnc.logger import get_logger

log = get_logger(__name__)


app = typer.Typer()


@app.command("version")
def version_info(
    ctx: typer.Context,
):
    send_event("info.version")

    def get_version_from_pyproject():
        # Get the directory of the current file
        dir_path = os.path.dirname(os.path.realpath(__file__))
        # Go two directories up
        dir_path = os.path.dirname(os.path.dirname(os.path.dirname(dir_path)))
        # Construct the full path to the pyproject.toml file
        file_path = os.path.join(dir_path, "pyproject.toml")

        with open(file_path, "r") as f:
            pyproject = toml.load(f)
        return pyproject["tool"]["poetry"]["version"]

    version = get_version_from_pyproject()
    print(f"{version}")
    raise typer.Exit()


@app.command("app")
def application_info(
    ctx: typer.Context,
):
    send_event("info.app")
    app = ctx.obj.application

    data = {
        "name": app.name,
        "version": f"{app.provider}/{app.flavor}/{app.version}",
        "collections": ",".join([c.name for c in app.collections]),
    }

    headers = list(data.keys())
    table_data = [list(data.values())]

    print(tabulate(table_data, headers, tablefmt="grid"))

    raise typer.Exit()


@app.command()
def environments(
    ctx: typer.Context,
    collection_name: str = "",
):
    send_event("info.environments")
    collection = (
        ctx.obj.application.collection_by_name(collection_name)
        or ctx.obj.application.default_collection
    )
    if not collection:
        log.error(f"No collection found for: {collection_name}")
        raise typer.Exit(code=1)

    env_datas = []
    for environment in collection.environments:
        env_datas.append(environment.collection.cli_info_for_environment(environment))

    if env_datas:
        headers = list(env_datas[0].keys())
        table_data = [list(d.values()) for d in env_datas]
        print(tabulate(table_data, headers, tablefmt="grid"))
    else:
        print(f"No environments for {collection}")

    raise typer.Exit()


@app.command()
def services(
    ctx: typer.Context,
    environment_name: str,
    collection_name: str = "",
):
    send_event("info.services")
    collection = (
        ctx.obj.application.collection_by_name(collection_name)
        or ctx.obj.application.default_collection
    )
    if not collection:
        log.error(f"No collection found for: {collection_name}")
        raise typer.Exit(code=1)

    environment = collection.environment_by_name(environment_name)
    if not environment:
        log.error(f"No environment found for: {environment_name}")
        raise typer.Exit(code=1)

    svc_datas = []
    for service in environment.services:
        svc_datas.append(service.cli_info())

    if svc_datas:
        headers = list(svc_datas[0].keys())
        table_data = [list(d.values()) for d in svc_datas]
        print(tabulate(table_data, headers, tablefmt="grid"))
    else:
        print(f"No services for {environment}")

    raise typer.Exit()
