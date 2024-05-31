import subprocess
from typing import List

from .cycle_stage_base import EnvironmentTemplatedBase
from cnc.logger import get_logger

log = get_logger(__name__)


class ToolboxManager(EnvironmentTemplatedBase):
    template_type = "toolbox"

    def __init__(self, service, service_tags=None):
        super().__init__(service.environment, service_tags)
        self.service = service

    @property
    def environment_items(self):
        if not hasattr(self, "_environment_items"):
            all_env_items = self.service.environment_items
            # Append toolbox env vars
            for resource in self.environment.config.resources:
                if not hasattr(
                    resource.settings,
                    "toolbox_managed_environment_variables",
                ):
                    continue

                for (
                    name,
                    value,
                ) in resource.settings.toolbox_managed_environment_variables.items():
                    # Remove existing var if it is being replaced
                    for i, env_item in enumerate(all_env_items):
                        if env_item.name == name:
                            del all_env_items[i]

                    all_env_items.append(
                        self.environment.config.variable_object(
                            {"name": name, "value": value}
                        )
                    )

            self._environment_items = all_env_items

        return self._environment_items

    def template_context(self, _service=None, command=None):
        return {
            "toolbox": self,
            "service": self.service,
            "environment": self.environment,
            "collection": self.collection,
            "bastion_instance_id": self.collection.get_terraform_output(
                "bastion_instance_id"
            ),
            "command": command,
        }

    def render_toolbox(self, command=None):
        context = self.template_context(command=command)
        context["render_template"] = self.write_template_with_context(self.service)
        self.write_template("main.sh.j2", context=context)

    def copy_templates(self):
        self.copy_template_dir()

    def start(self):
        log.debug(f"Rendering toolbox script for {self} @ {self.config_files_path}")
        self.setup()
        self.render_toolbox()
        log.debug(f"Done rendering toolbox script for {self}, starting toolbox...")

        try:
            ret = subprocess.run(
                [
                    "bash",
                    "-c",
                    (
                        f"chmod +x {self.rendered_files_path}/main.sh "
                        f"&& setsid {self.rendered_files_path}/main.sh"
                    ),
                ],
                executable="/bin/bash",
            )
            if ret.stdout or ret.stderr:
                log.debug(f"Output from main.sh: \n{ret.stdout}\n{ret.stderr}")
        except subprocess.CalledProcessError as e:
            # Handle any errors that occurred during script execution
            print(f"Error running the script: {e}")
            print("Error output:")
            print(e.stderr)

    def run(self, command: List[str] = []):
        log.debug(f"Rendering toolbox script for {self} @ {self.config_files_path}")
        self.setup()
        self.render_toolbox(command=" ".join(command))
        log.debug(f"Done rendering toolbox script for {self}, starting toolbox...")

        try:
            ret = subprocess.run(
                [
                    "bash",
                    "-c",
                    (
                        f"chmod +x {self.rendered_files_path}/main.sh "
                        f"&& setsid {self.rendered_files_path}/main.sh"
                    ),
                ],
                executable="/bin/bash",
            )
            if ret.stdout or ret.stderr:
                log.debug(f"Output from main.sh: \n{ret.stdout}\n{ret.stderr}")

            return ret.returncode
        except subprocess.CalledProcessError as e:
            # Handle any errors that occurred during script execution
            print(f"Error running the script: {e}")
            print("Error output:")
            print(e.stderr)
            return 1
