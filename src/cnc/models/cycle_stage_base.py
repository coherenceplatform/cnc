import os
import re
import subprocess
import shutil
from pathlib import Path
from functools import partial, cached_property

from jinja2 import (
    Environment,
    FileSystemLoader,
    select_autoescape,
    StrictUndefined,
)

from cnc.logger import get_logger

log = get_logger(__name__)


class _TemplatedBase:
    template_type = "build"
    entrypoint_script_name = "main.sh.j2"

    def __repr__(self):
        return f"<{self.__class__.__name__} @ {self.working_dir} -> {self.config_files_path}>"

    __str__ = __repr__

    @property
    def config_files_path(self):
        return f"{self.collection.config_files_path}/{self.template_type}"

    @property
    def rendered_files_path(self):
        return f"{self.config_files_path}/_cnc_output"

    @property
    def custom_template_dir(self):
        return f"{self.config_files_path}/custom"

    def setup(self):
        if not os.path.isdir(self.config_files_path):
            os.makedirs(self.config_files_path, exist_ok=True)

        if not os.path.isdir(self.rendered_files_path):
            os.makedirs(self.rendered_files_path, exist_ok=True)

        if self.template_config.enabled:
            if not os.path.isdir(self.custom_template_dir):
                os.makedirs(self.custom_template_dir, exist_ok=True)

        self.copy_templates()
        return True

    def copy_template_dir(self):
        src_dir = Path(__file__).parent.parent
        cwd = self.working_dir

        # Path to the directory where templates are finally consolidated
        final_template_dir = self.config_files_path

        # Copy shared default templates
        shared_template_dir = (
            f"{src_dir}/flavors/{self.application.provider}"
            f"/shared/{self.template_type}"
        )
        if os.path.isdir(shared_template_dir):
            shutil.copytree(
                shared_template_dir,
                final_template_dir,
                dirs_exist_ok=True,
            )

        # Copy flavor-specific templates, which can overwrite shared defaults
        flavor_dir = (
            f"{src_dir}/flavors/{self.application.provider}/"
            f"{self.application.flavor}/{self.application.version}"
            f"/{self.template_type}"
        )
        if os.path.isdir(flavor_dir):
            shutil.copytree(
                flavor_dir,
                final_template_dir,
                dirs_exist_ok=True,
            )

        # Copy custom templates if enabled, which can overwrite any of the defaults
        if self.template_config.enabled:
            custom_template_dir = Path(
                f"{cwd}/{self.template_config.template_directory}"
            )
            main_file = getattr(
                self.template_config, f"{self.template_type}_filename", None
            )

            if not custom_template_dir.is_dir():
                raise Exception(
                    f"Template directory {custom_template_dir} does not exist"
                )

            shutil.copytree(
                str(custom_template_dir),
                self.custom_template_dir,
                dirs_exist_ok=True,
            )

            # Check if the custom main template file exists
            path_to_copy = Path(
                f"{custom_template_dir}/{self.template_type}/{main_file}"
            )
            if path_to_copy.is_file():
                # Optionally delete an entrypoint script in the final directory before copying the main file
                entry_script_path = Path(
                    f"{final_template_dir}/{self.entrypoint_script_name}"
                )
                if entry_script_path.exists():
                    os.remove(entry_script_path)
                shutil.copy(
                    str(path_to_copy),
                    f"{str(final_template_dir)}/{self.entrypoint_script_name}",
                )

        return True

    def get_template(self, name, template_directory=None):
        template_directory = template_directory or self.config_files_path
        env = Environment(
            loader=FileSystemLoader(template_directory),
            autoescape=select_autoescape(),
            undefined=StrictUndefined,
        )

        try:
            return env.get_template(name)
        except Exception as e:
            log.warning(f"Could not get template ({name}): {e}")
            self.debug_template_output_directory(template_directory)
            raise e

    def cleanup(self):
        shutil.rmtree(
            self.config_files_path,
            ignore_errors=True,
        )
        return True

    def template_context(self):
        return {}

    def write_template(
        self,
        name,
        output_name=None,
        context=None,
        additional_context=None,
        template_directory=None,
    ):
        template = self.get_template(name, template_directory)
        if not template:
            log.info(f"No template for {name} for {self}")
            return

        output_name = output_name or ".".join(name.split(".")[:-1])
        output_path = f"{self.rendered_files_path}/{output_name}"
        with open(output_path, "w") as f:
            # render template
            template_context = context or self.template_context()
            template_context.update(additional_context or {})
            rendered = template.render(**template_context)
            # strip excess newlines
            cleaned = re.sub(r"\n\s*\n", "\n", rendered)
            f.write(cleaned)

        return True

    def _wrapped_write_template(self, *args, **kwargs):
        self.write_template(*args, **kwargs)
        return ""

    def write_template_with_context(self, service):
        return partial(
            self._wrapped_write_template, context=self.template_context(service)
        )

    def debug_template_output(self, output_name):
        try:
            print(
                f"\n\n---------CONTENTS of {output_name}---------\n\n"
                + open(f"{self.config_files_path}/_cnc_output/{output_name}").read()
                + f"\n\n---------END OF CONTENTS for {output_name}---------\n\n"
            )
        except FileNotFoundError as e:
            log.error(f"File {output_name} not found: {e}")
            return False

    def debug_template_output_directory(self, template_directory=None):
        template_directory = template_directory or f"{self.rendered_files_path}"
        log.debug(f"\noutput directory is: {template_directory}\n")
        subprocess.run(["ls", "-alhR", f"{template_directory}"])

    def debug_template_directory(self, template_directory=None):
        template_directory = template_directory or f"{self.config_files_path}"
        log.debug(f"\ndirectory is: {template_directory}\n")
        subprocess.run(["ls", "-alhR", f"{template_directory}"])

    def file_exists(self, file_path="Dockerfile"):
        return os.path.isfile(f"{self.working_dir}/{file_path}")


class CollectionTemplatedBase(_TemplatedBase):
    def __init__(
        self,
        collection,
    ):
        self.application = collection.application
        self.collection = collection
        self.template_config = self.application.template_config
        self.working_dir = os.getcwd()

    def __repr__(self):
        return f"<{self.__class__.__name__}: {self.collection} | output_only: {self.output_only}>"

    __str__ = __repr__

    @cached_property
    def environment_items(self):
        _all = {}

        for environment in self.collection.environments:
            for item in environment.environment_items:
                _all.update({item.name: item.value})

        return _all


class EnvironmentTemplatedBase(_TemplatedBase):
    def __init__(
        self,
        environment,
        service_tags=None,
        default_tag="latest",
    ):
        self.environment = environment

        if isinstance(service_tags, list):
            service_tags = {
                tag.split("=")[0]: tag.split("=")[1] for tag in service_tags
            }

        self.service_tags = service_tags or {}
        self.collection = environment.collection
        self.application = environment.application
        self.template_config = self.application.template_config
        self.scripts_to_run = []

        self.working_dir = os.getcwd()
        self.default_tag = default_tag or "latest"

    def __repr__(self):
        return f"<{self.__class__.__name__}:{self.environment} @ {self.service_tags}>"

    __str__ = __repr__

    @cached_property
    def environment_items(self):
        _all = {}

        for item in self.environment.environment_items:
            _all.update({item.name: item.value})

        return _all

    def copy_templates(self):
        self.copy_template_dir()

    def tag_for_service(self, service_name=None):
        return self.service_tags.get(service_name, self.default_tag)
