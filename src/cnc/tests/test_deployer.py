from .base_test_class import CNCBaseTestCase
from cnc.models import Application, DeployStageManager


from cnc.logger import get_logger

log = get_logger(__name__)


class DeployStageTestBase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"
    environment_name = "main"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml(self.env_data_filepath)
        collection = app.collections[0]
        collection._infra_outputs_cache = {}

        self.environment = collection.environment_by_name(self.environment_name)
        self.assertEqual(self.environment_name, self.environment.name)

        self.deployer = DeployStageManager(self.environment)

        self.deployer.cleanup()
        self.deployer.setup()
        self.deployer.render_scripts()

    def tearDown(self):
        super().tearDown()
        if hasattr(self, "deployer"):
            self.deployer.cleanup()

    def parse(self, script_name="build.sh"):
        with open(f"{self.deployer.rendered_files_path}/{script_name}", "r") as file:
            return file.read()


class AWSDeployStageTestBase(DeployStageTestBase):
    env_data_filepath = "environments_aws_ecs.yml"

    def setUp(self):
        super().setUp()
        self.assertTrue(self.environment.application.provider_is_aws)


class DeployStageCustomTestBase(DeployStageTestBase):
    fixture_name = "backend-1-service-custom"

    def setUp(self):
        super().setUp()

    def test_custom_template(self):
        build = self.parse("deploy-app.sh")
        self.assertIn("custom_template", build)


class AWSDeployStageSmokeTest(AWSDeployStageTestBase):
    def test_deploy_functions(self):
        build = self.parse("deploy-app.sh")
        self.assertNotIn("deploy_app_scheduled_tasks", build)
        self.assertNotIn("deploy_app_workers_to_ecs", build)
        self.assertIn(
            (
                f"source { self.deployer.rendered_files_path }/deploy-"
                "app-functions.sh"
            ),
            build,
        )
        self.assertIn("deploy_app_to_ecs", build)
        self.assertIn("check_app_ecs_service_deploy_status", build)

        build_functions = self.parse("deploy-app-functions.sh")
        self.assertNotIn("deploy_app_scheduled_tasks", build_functions)
        self.assertNotIn("deploy_app_workers_to_ecs", build_functions)
        self.assertIn("deploy_app_to_ecs", build_functions)
        self.assertIn("check_app_ecs_service_deploy_status", build_functions)

        for service in self.environment.web_services:
            web_task = self.parse(f"ecs-web-{service.name}.json")
            self.assertIn(service.instance_name, web_task)
