import subprocess

from .cycle_stage_base import EnvironmentTemplatedBase
from .stage import Stage

from cnc.logger import get_logger

log = get_logger(__name__)


class BuildStageManager(EnvironmentTemplatedBase):
    template_type = "build"

    def __init__(self, *args, webhook_url=None, webhook_token=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.webhook_url = webhook_url
        self.webhook_token = webhook_token

    def template_context(self, service):
        return {
            "builder": self,
            "service": service,
            "environment": self.environment,
            "stage": Stage.model_validate({"name": "build"}),
            "load_database_snapshot": False,
        }

    def debug(self):
        self.debug_template_output_directory()

        for script in self.scripts_to_run:
            self.debug_template_output(script)

        for service in self.environment.services:
            self.debug_template_output(f"build-{service.name}-functions.sh")

        log.debug(f"All done with debug for {self}")
        return

    def render_build(self, service_names=None):
        for service in self.environment.services:
            if service_names:
                if service.name not in service_names:
                    continue

            if service.settings.is_resource:
                continue

            context = self.template_context(service)
            context["render_template"] = self.write_template_with_context(service)

            self.write_template(
                "build_functions.sh.j2",
                output_name=f"build-{service.name}-functions.sh",
                context=context,
            )

            service_build_script_name = f"build-{service.name}.sh"
            self.write_template(
                "main.sh.j2", output_name=service_build_script_name, context=context
            )
            self.scripts_to_run.append(service_build_script_name)

    def perform(self, should_cleanup=True, should_regenerate_config=True, debug=False):
        log.debug(f"Performing build for {self} @ {self.config_files_path}")
        if should_cleanup:
            self.cleanup()

        self.setup()

        if should_regenerate_config:
            self.render_build(service_names=self.service_tags.keys())
            log.debug(
                f"Done rendering build for {self} (svcs: {self.service_tags.keys()}), going to execute..."
            )

        if debug:
            self.debug()
            return

        for script in self.scripts_to_run:
            # self.debug_template_output(script)
            # self.debug_template_output(f"build-app-functions.sh")

            try:
                # log.debug(f"Going to run {script}...")
                ret = subprocess.run(
                    ["bash", "-c", f"source {self.rendered_files_path}/{script}"],
                    executable="/bin/bash",
                )
                # log.debug(f"Output from {script}: \n{ret.stdout}\n{ret.stderr}")
                if ret.returncode != 0:
                    return ret.returncode

                log.info(f"All done with perform for {self}")
            except subprocess.CalledProcessError as e:
                # Handle any errors that occurred during script execution
                print(f"Error running the script: {e}")
                print("Error output:")
                print(e.stderr)
                return 1

        return 0
