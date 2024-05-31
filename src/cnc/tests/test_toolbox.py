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
