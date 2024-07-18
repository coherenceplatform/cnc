import shlex

from unittest.mock import patch

from .base_test_class import CNCBaseTestCase
from cnc.models import (
    ToolboxManager,
    Application,
)
from cnc.logger import get_logger

log = get_logger(__name__)


class BaseToolboxTest(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"
    environment_tag = "latest"
    env_data_filepath = "environments.yml"
    proxy_only = False

    def setUp(self):
        super().setUp()
        self.app = Application.from_environments_yml(
            self.env_data_filepath,
        )
        self.collection = self.app.collections[0]
        self.collection._infra_outputs_cache = {}

        self.environment = self.collection.environments[0]
        self.service = self.environment.backend_services[0]

        self.toolbox = ToolboxManager(
            service=self.service,
            service_tags={self.service.name: self.environment_tag},
            proxy_only=self.proxy_only,
        )

        self.toolbox.setup()
        with patch.object(
            self.collection.__class__,
            "get_secret_value",
            return_value="secretvalue",
        ):
            self.toolbox.render_toolbox()

    def tearDown(self):
        super().tearDown()
        if hasattr(self, "toolbox"):
            self.toolbox.cleanup()

    def parse(self, script_name="main.sh"):
        with open(
            f"{self.toolbox.rendered_files_path}/{script_name}",
            "r",
        ) as file:
            return file.read()


class AWSToolboxSmokeTest(BaseToolboxTest):
    env_data_filepath = "environments_aws_ecs.yml"

    def test_toolbox_render(self):
        toolbox_script = self.parse()
        self.assertIn("aws ssm start-session", toolbox_script)

        dockerfile = self.parse("Dockerfile")
        self.assertIn(
            f"{self.service.image_for_tag(self.environment_tag)}",
            dockerfile,
        )


class AWSToolboxProxyOnlySmokeTest(BaseToolboxTest):
    env_data_filepath = "environments_aws_ecs.yml"
    proxy_only = True

    def test_toolbox_render(self):
        toolbox_script = self.parse()
        self.assertIn("aws ssm start-session", toolbox_script)
        self.assertNotIn("docker", toolbox_script)


class GCPToolboxSmokeTest(BaseToolboxTest):
    env_data_filepath = "environments.yml"

    def test_toolbox_render(self):
        toolbox_script = self.parse()
        self.assertIn("compute ssh toolbox@", toolbox_script)

        dockerfile = self.parse("Dockerfile")
        self.assertIn(
            f"{self.service.image_for_tag(self.environment_tag)}",
            dockerfile,
        )


class GCPToolboxProxyOnlySmokeTest(BaseToolboxTest):
    env_data_filepath = "environments.yml"
    proxy_only = True

    def test_toolbox_render(self):
        toolbox_script = self.parse()
        self.assertIn("compute ssh toolbox@", toolbox_script)
        self.assertNotIn("docker", toolbox_script)


class SpecialCharactersInVarsTest(BaseToolboxTest):
    env_data_filepath = "environments_weird_character_vars.yml"

    def test_toolbox_render(self):
        toolbox_script = self.parse()

        # Check for each environment variable in the docker run command
        self.assertIn("FOO=" + shlex.quote("bar"), toolbox_script)
        self.assertIn("FOO_JSON=" + shlex.quote('{"foo": "bar"}'), toolbox_script)
        self.assertIn(
            "FOO_SPECIALS=" + shlex.quote("foo!\"'`@#$%^&*()_+bar\\\n"), toolbox_script
        )
        self.assertIn(
            "COMPLEX_JSON="
            + shlex.quote('{"key1": ["value1", "value2"], "key2": {"nested": true}}'),
            toolbox_script,
        )
        self.assertIn(
            "MULTILINE=" + shlex.quote("line1 line2\tindented\n"), toolbox_script
        )
        self.assertIn(
            "COMPLEX_PASSWORD=" + shlex.quote("P@ssw0rd!#$%^&*()_+{}[]|\\/?,.<>~`"),
            toolbox_script,
        )

        # Check for other important parts of the script
        self.assertIn("#!/bin/bash", toolbox_script)
        self.assertIn(
            "TOOLBOX_ACTIVE_TEMP_FILEPATH=/tmp/cnc_toolbox_active", toolbox_script
        )
        self.assertIn("trap cleanup_toolbox EXIT", toolbox_script)
        self.assertIn("gcloud auth configure-docker", toolbox_script)
        self.assertIn("start_resource_port_forwarding", toolbox_script)
