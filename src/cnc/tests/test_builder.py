from unittest.mock import patch

from .base_test_class import CNCBaseTestCase
from cnc.models import Application, BuildStageManager
from cnc.models.providers.google.environment_collection import GCPEnvironmentCollection


from cnc.logger import get_logger

log = get_logger(__name__)


class BuildTemplateConfigTest(CNCBaseTestCase):
    fixture_name = "backend-1-service"

    def test_template_config(self):
        app = Application.from_environments_yml("environments.yml")
        self.assertEqual(app.template_config.enabled, False)

        app = Application.from_environments_yml("environments-custom-provision.yml")
        self.assertEqual(app.template_config.enabled, True)
        self.assertEqual(app.template_config.template_directory, "custom")
        self.assertEqual(app.template_config.provision_filename, "main.tf.j2")
        self.assertEqual(app.template_config.deploy_filename, "main.sh.j2")
        self.assertEqual(app.template_config.build_filename, "main.sh.j2")


class BuildTagsPerServiceTestCase(CNCBaseTestCase):
    fixture_name = "backend-2-service-1-db"

    def test_template_config_tags(self):
        app = Application.from_environments_yml("environments.yml")
        environment = app.collections[0].environments[0]
        svc1 = environment.web_services[0]
        svc2 = environment.web_services[1]

        builder = BuildStageManager(environment, {svc1.name: "tag1", svc2.name: "tag2"})
        builder.cleanup()
        builder.setup()

        with patch.object(
            GCPEnvironmentCollection, "get_secret_value", return_value="secretvalue"
        ):
            builder.render_build()

        with open(f"{builder.rendered_files_path}/build-app-functions.sh", "r") as file:
            app_build_functions = file.read()

        with open(f"{builder.rendered_files_path}/build-api-functions.sh", "r") as file:
            api_build_functions = file.read()

        self.assertIn(
            f"us-east1-docker.pkg.dev/foo-bar-123/{environment.collection.instance_name}/my-backend-t-app:tag1",
            app_build_functions,
        )
        self.assertIn(
            f"us-east1-docker.pkg.dev/foo-bar-123/{environment.collection.instance_name}/my-backend-t-api:tag2",
            api_build_functions,
        )

        builder.cleanup()


class GCPBuildStageTestBase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"
    environment_name = "main"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml("environments.yml")
        collection = app.collections[0]

        self.environment = collection.environment_by_name(self.environment_name)
        self.assertEqual(self.environment_name, self.environment.name)

        self.manager = BuildStageManager(self.environment)

        self.manager.cleanup()
        self.manager.setup()
        with patch.object(
            GCPEnvironmentCollection, "get_secret_value", return_value="secretvalue"
        ):
            self.manager.render_build()

    def tearDown(self):
        super().tearDown()
        if hasattr(self, "manager"):
            self.manager.cleanup()

    def parse(self, script_name="build.sh"):
        with open(f"{self.manager.rendered_files_path}/{script_name}", "r") as file:
            return file.read()


class GCPBuildStageSmokeTest(GCPBuildStageTestBase):
    def test_build_functions(self):
        build = self.parse("build-app.sh")
        self.assertNotIn("run_image", build)
        self.assertNotIn("verify_app_image_exists", build)
        self.assertIn("build_app_image", build)

        build_functions = self.parse("build-app-functions.sh")
        self.assertNotIn("run_image", build)
        self.assertIn("verify_app_image_exists", build_functions)
        self.assertIn("build_app_image ()", build_functions)
        self.assertIn("build_app_image ()", build_functions)


class AWSBuildStageTestBase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"
    environment_name = "main"
    env_data_filepath = "environments_aws_ecs.yml"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml(self.env_data_filepath)
        collection = app.collections[0]

        self.environment = collection.environment_by_name(self.environment_name)
        self.assertEqual(self.environment_name, self.environment.name)

        self.manager = BuildStageManager(self.environment)

        self.manager.cleanup()
        self.manager.setup()
        self.manager.render_build()

    def tearDown(self):
        super().tearDown()
        if hasattr(self, "manager"):
            self.manager.cleanup()

    def parse(self, script_name="build.sh"):
        with open(f"{self.manager.rendered_files_path}/{script_name}", "r") as file:
            return file.read()


class AWSBuildStageSmokeTest(AWSBuildStageTestBase):
    def test_build_functions(self):
        self.assertTrue(self.environment.application.provider_is_aws)

        build = self.parse("build-app.sh")
        self.assertNotIn("run_image", build)
        self.assertNotIn("verify_app_image_exists", build)
        self.assertIn("build_app_image", build)

        build_functions = self.parse("build-app-functions.sh")
        self.assertNotIn("run_image", build_functions)
        self.assertNotIn("verify_app_image_exists", build_functions)
        self.assertIn("build_app_image ()", build_functions)
