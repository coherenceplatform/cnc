import os
import typer
import click
import pprint
from jinja2.visitor import NodeVisitor

from jinja2 import (
    meta,
    Environment,
    FileSystemLoader,
    select_autoescape,
    StrictUndefined,
)

from cnc.models.cycle_stage_base import _TemplatedBase

from cnc.logger import get_logger

log = get_logger(__name__)


app = typer.Typer()


class TemplateNodeInspector(NodeVisitor):
    def __init__(self):
        self.found_extends = []
        self.found_includes = []

    def visit_Extends(self, node):
        self.found_extends.append(node.template.as_const())
        super().generic_visit(node)

    def visit_Include(self, node):
        self.found_includes.append(node.template.as_const())
        super().generic_visit(node)


def find_blocks(node, blocks=None):
    """Recursively find block names in the template AST."""
    if blocks is None:
        blocks = set()

    # Check if the node is a Block node and add it to the blocks set
    if isinstance(node, meta.nodes.Block):
        blocks.add(node.name)

    # If the node has a body attribute, iterate over its contents
    if hasattr(node, "body"):
        # For nodes with a body that is a list (e.g., Template, Block)
        if isinstance(node.body, list):
            for subnode in node.body:
                find_blocks(subnode, blocks)
        # For nodes with a single node as a body (not in a list)
        elif isinstance(node.body, meta.nodes.Node):
            find_blocks(node.body, blocks)

    # Additionally, for nodes representing control structures that have
    # an `else` or `elif` block, we also need to check these blocks.
    if hasattr(node, "elif_"):
        for condition, body in node.elif_:
            find_blocks(body, blocks)
    if hasattr(node, "else_") and node.else_:
        find_blocks(node.else_, blocks)

    return blocks


class TemplateInspector(_TemplatedBase):
    def __init__(self, collection, template_type="build"):
        self.application = collection.application
        self.collection = collection
        self.template_config = self.application.template_config
        self.working_dir = os.getcwd()
        self.template_type = template_type

    def get_parsed_template(self, template_name):
        env = Environment(
            loader=FileSystemLoader(self.config_files_path),
            autoescape=select_autoescape(),
            undefined=StrictUndefined,
        )
        template_source = env.loader.get_source(env, template_name)[0]
        return env.parse(template_source)

    def find_variables(self, ast):
        """Find undeclared variables in the template AST."""
        return meta.find_undeclared_variables(ast)

    def find_extends_and_includes(self, ast):
        """Find all extends and includes within an AST."""
        extends = [
            node.template.value
            for node in ast.body
            if node.__class__.__name__ == "Extends"
        ]
        includes = [
            node.template.value
            for node in ast.body
            if node.__class__.__name__ == "Include"
        ]
        return extends, includes

    def analyze_template(self, template_name, analyzed_templates=set()):
        if template_name in analyzed_templates:
            return set()

        analyzed_templates.add(template_name)

        ast = self.get_parsed_template(template_name)
        inspector = TemplateNodeInspector()
        inspector.visit(ast)

        variables = set(self.find_variables(ast))

        # Recursively analyze base templates
        for base_template in inspector.found_extends:
            variables.update(self.analyze_template(base_template, analyzed_templates))

        # Recursively analyze included templates
        for included_template in inspector.found_includes:
            variables.update(
                self.analyze_template(included_template, analyzed_templates)
            )

        return variables

    def inspect_template_context(self):
        _context = {}

        for service in self.collection.all_services_for_type():
            context_kwargs = {}

            if self.template_type == "build":
                from cnc.models import BuildStageManager

                manager = BuildStageManager(self.collection.environments[0])
                context_kwargs = {"service": service}
            elif self.template_type == "deploy":
                from cnc.models import DeployStageManager

                manager = DeployStageManager(self.collection)
                context_kwargs = {"service": service}
            elif self.template_type == "provision":
                from cnc.models.provisioner import ProvisionStageManager

                manager = ProvisionStageManager(self.collection)

            _context[service.name] = manager.template_context(**context_kwargs)
        return _context

    def inspect(self, template_name):
        self.copy_template_dir()
        self.debug_template_directory()

        ast = self.get_parsed_template(template_name)
        blocks = find_blocks(ast)
        variables = self.analyze_template(template_name)
        context = self.inspect_template_context()

        print(f"Blocks: {blocks}")
        print(f"Accessed Variables: {variables}")
        pprint.pprint(context)

        self.cleanup()


@app.command("list")
def list_for_file(
    ctx: typer.Context,
    template_path: str,
    collection_name: str = "",
    template_type: str = typer.Option(
        default="provision", click_type=click.Choice(["build", "provision", "deploy"])
    ),
):
    collection = ctx.obj.application.collection_by_name(collection_name)
    if not collection:
        log.error(f"No collection found for: {collection_name}")
        raise typer.Exit(code=1)

    inspector = TemplateInspector(collection)
    inspector.template_type = template_type
    inspector.inspect(template_path)

    raise typer.Exit()
