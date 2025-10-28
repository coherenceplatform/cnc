import yaml
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


class GCPDeployWithJsonVarsTest(DeployStageTestBase):
    fixture_name = "backend-1-service"
    env_data_filepath = "environments_json_var.yml"

    def test_render_json_in_run_template(self):
        run_yml = self.parse("run-app.yml")
        self.assertTrue(isinstance(yaml.safe_load(run_yml), dict))


class AWSDeployStageSmokeTest(AWSDeployStageTestBase):
    def test_deploy_functions(self):
        build = self.parse("deploy-app.sh")
        self.assertNotIn("deploy_app_scheduled_tasks", build)
        self.assertNotIn("deploy_app_workers_to_ecs", build)
        self.assertIn(
            (f"source {self.deployer.rendered_files_path}/deploy-" "app-functions.sh"),
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


class UpdateExitCodeTest(DeployStageTestBase):
    """Test that update command properly propagates exit codes on failure"""

    def test_update_command_ignores_deploy_failure_exit_code(self):
        """Test that demonstrates the bug where update.py doesn't propagate deploy failures

        This test shows that when deployer.perform() returns a non-zero exit code,
        the update command ignores it and always exits with 0.
        """
        from unittest.mock import patch, MagicMock
        from cnc.commands.update import perform
        import typer

        # Mock the context and application
        mock_ctx = MagicMock()
        mock_application = MagicMock()
        mock_collection = MagicMock()
        mock_environment = MagicMock()

        mock_application.collection_by_name.return_value = mock_collection
        mock_collection.environment_by_name.return_value = mock_environment
        mock_ctx.obj.application = mock_application

        # Mock BuildStageManager to succeed
        with patch("cnc.commands.update.BuildStageManager") as mock_build_class, patch(
            "cnc.commands.update.DeployStageManager"
        ) as mock_deploy_class, patch(
            "cnc.commands.update.send_event"
        ):  # Mock telemetry

            mock_builder = MagicMock()
            mock_builder.perform.return_value = 0  # Build succeeds
            mock_build_class.return_value = mock_builder

            mock_deployer = MagicMock()
            mock_deployer.perform.return_value = 42  # Deploy fails with exit code 42
            mock_deploy_class.return_value = mock_deployer

            # Call the perform function and expect it to raise typer.Exit
            with self.assertRaises(typer.Exit) as cm:
                perform(
                    ctx=mock_ctx,
                    environment_name="main",
                    collection_name="test",
                    service_tags=[],
                    default_tag=None,
                    cleanup=True,
                    debug=False,
                    generate=True,
                )

            # The exit code should be 42 (from deploy failure), not 0
            # This will FAIL with the current bug, showing exit code is 0
            exit_code = cm.exception.exit_code
            self.assertNotEqual(
                exit_code,
                0,
                f"Expected non-zero exit code from failed deploy in update command, got {exit_code}. "
                f"This demonstrates the bug where update.py ignores deployer.perform() exit code.",
            )
            self.assertEqual(
                exit_code,
                42,
                f"Expected exit code 42 from failed deploy in update command, got {exit_code}",
            )
