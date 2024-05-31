from unittest.mock import patch
import os

from .base_test_class import CNCBaseTestCase
from cnc.models import Application, ProvisionStageManager

from cnc.logger import get_logger

log = get_logger(__name__)


class ProvisionStageSmokeTest(CNCBaseTestCase):
    fixture_name = "backend-1-service"

    def test_tf_is_valid(self):
        app = Application.from_environments_yml(self.env_data_filepath)
        self.assertEqual(len(app.collections), 1)

        collection = app.collections[0]
        collection._infra_outputs_cache = {}
        self.assertEqual(collection.name, "preview")

        self.manager = ProvisionStageManager(collection)
        with patch.object(
            collection.__class__,
            "get_secret_value",
            return_value="secretvalue",
        ):
            self.assertTrue(self.manager.make_ready_for_use())

        self.assertTrue(self.manager.validate())

    def tearDown(self):
        if hasattr(self, "manager"):
            self.manager.cleanup()


class ProvisionStageCleanupSettingsTest(CNCBaseTestCase):
    fixture_name = "backend-1-service"

    def test_provision_cleanup(self):
        app = Application.from_environments_yml(self.env_data_filepath)
        self.assertEqual(len(app.collections), 1)

        collection = app.collections[0]
        collection._infra_outputs_cache = {}
        self.assertEqual(collection.name, "preview")

        manager = ProvisionStageManager(collection)
        self.addCleanup(manager.cleanup)

        manager.make_ready_for_use()
        self.assertEqual(
            sorted(os.listdir(manager.config_files_path)),
            ["_cnc_output", "base.tf.j2", "main.tf.j2", "partials"],
        )

        sample_path = f"{manager.config_files_path}/newfile.txt"
        with open(sample_path, "w") as file:
            file.write("Hello, World!")
        manager.make_ready_for_use()
        self.assertEqual(
            sorted(os.listdir(manager.config_files_path)),
            ["_cnc_output", "base.tf.j2", "main.tf.j2", "partials"],
        )

        with open(sample_path, "w") as file:
            file.write("Hello, World!")
        manager.make_ready_for_use(should_cleanup=False)
        self.assertEqual(
            sorted(os.listdir(manager.config_files_path)),
            ["_cnc_output", "base.tf.j2", "main.tf.j2", "newfile.txt", "partials"],
        )

        with open(f"{manager.config_files_path}/_cnc_output/main.tf", "w") as file:
            file.write("Hello, World!")
        manager.make_ready_for_use(should_cleanup=False, should_regenerate_config=False)
        self.assertEqual(
            open(f"{manager.config_files_path}/_cnc_output/main.tf").read(),
            "Hello, World!",
        )


class AWSProvisionStageSmokeTest(ProvisionStageSmokeTest):
    env_data_filepath = "environments_aws_ecs.yml"


class ProvisionStageTestBase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml(self.env_data_filepath)
        collection = app.collections[0]
        collection._infra_outputs_cache = {}
        self.manager = ProvisionStageManager(collection)
        with patch.object(
            collection.__class__,
            "get_secret_value",
            return_value="secretvalue",
        ):
            self.assertTrue(self.manager.make_ready_for_use())
        self.assertTrue(self.manager.validate())

        parsed = self.manager.parse_config_file()
        self.resources = parsed.get("resource", {})

    def tearDown(self):
        super().tearDown()
        if hasattr(self, "manager"):
            self.manager.cleanup()


class GCPProvisionStageOneResourceTest(ProvisionStageTestBase):
    def test_database_count(self):
        self.assertEqual(
            len(self.resources.get("google_compute_backend_service", [])), 2
        )
        self.assertEqual(len(self.resources.get("google_cloud_run_service", [])), 2)
        self.assertEqual(
            len(self.resources.get("google_artifact_registry_repository", [])), 1
        )
        self.assertEqual(
            len(self.resources.get("google_compute_managed_ssl_certificate", [])), 1
        )
        self.assertEqual(len(self.resources.get("google_compute_network", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_database_instance", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_database", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_user", [])), 1)


class GCPProvisionStageTwoResourcesTest(ProvisionStageTestBase):
    fixture_name = "backend-1-service-2-db"

    def test_database_count(self):
        self.assertEqual(len(self.resources.get("google_cloud_run_service", [])), 2)
        self.assertEqual(len(self.resources.get("google_sql_database_instance", [])), 2)
        self.assertEqual(len(self.resources.get("google_sql_database", [])), 2)
        self.assertEqual(len(self.resources.get("google_sql_user", [])), 2)


class GCPProvisionStageTwoServicesTest(ProvisionStageTestBase):
    fixture_name = "backend-2-service-1-db"

    def test_database_count(self):
        self.assertEqual(len(self.resources.get("google_cloud_run_service", [])), 3)
        self.assertEqual(len(self.resources.get("google_sql_database_instance", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_database", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_user", [])), 1)


class GCPProvisionStageTwoServicesandDBsTest(ProvisionStageTestBase):
    fixture_name = "backend-2-service-2-db"

    def test_database_count(self):
        self.assertEqual(len(self.resources.get("google_cloud_run_service", [])), 3)
        self.assertEqual(len(self.resources.get("google_sql_database_instance", [])), 2)
        self.assertEqual(len(self.resources.get("google_sql_database", [])), 2)
        self.assertEqual(len(self.resources.get("google_sql_user", [])), 2)


class GCPProvisionStageTwoServicesandDBsTwoEnvsTest(ProvisionStageTestBase):
    fixture_name = "backend-1-service-2-db-2-envs"

    def test_database_count(self):
        self.assertEqual(len(self.resources.get("google_cloud_run_service", [])), 3)
        self.assertEqual(len(self.resources.get("google_sql_database_instance", [])), 4)

        log.debug(self.resources.get("google_sql_database"))

        self.assertEqual(len(self.resources.get("google_sql_database", [])), 4)
        self.assertEqual(len(self.resources.get("google_sql_user", [])), 4)


class GCPRunLiteProvisionStageOneResourceTest(ProvisionStageTestBase):
    env_data_filepath = "environments_gcp_run_lite.yml"

    def test_database_count(self):
        self.assertIsNone(self.resources.get("google_compute_backend_service"))
        self.assertEqual(len(self.resources.get("google_cloud_run_service", [])), 1)
        self.assertEqual(
            len(self.resources.get("google_artifact_registry_repository", [])), 1
        )
        self.assertIsNone(self.resources.get("google_compute_managed_ssl_certificate"))
        self.assertIsNone(self.resources.get("google_compute_network"))
        self.assertEqual(len(self.resources.get("google_sql_database_instance", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_database", [])), 1)
        self.assertEqual(len(self.resources.get("google_sql_user", [])), 1)


class AWSProvisionStageTestBase(ProvisionStageTestBase):
    env_data_filepath = "environments_aws_ecs.yml"


class AWSProvisionStageOneResourceTest(AWSProvisionStageTestBase):
    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 1)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 1)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 1)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 1)
        self.assertEqual(len(self.resources["aws_vpc"]), 1)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)


class AWSProvisionStageTwoResourcesTest(AWSProvisionStageTestBase):
    fixture_name = "backend-1-service-2-db"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 2)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 2)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 1)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 1)
        self.assertEqual(len(self.resources["aws_vpc"]), 1)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)


class AWSProvisionStageTwoServicesTest(AWSProvisionStageTestBase):
    fixture_name = "backend-2-service-1-db"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 1)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 1)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 2)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 2)
        self.assertEqual(len(self.resources["aws_vpc"]), 1)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)


class AWSProvisionStageTwoServicesandDBsTest(AWSProvisionStageTestBase):
    fixture_name = "backend-2-service-2-db"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 2)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 2)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 2)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 2)
        self.assertEqual(len(self.resources["aws_vpc"]), 1)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)


class AWSProvisionStageTwoServicesandDBsTwoEnvsTest(AWSProvisionStageTestBase):
    fixture_name = "backend-1-service-2-db-2-envs"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 4)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 4)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 2)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 2)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 2)
        self.assertEqual(len(self.resources["aws_vpc"]), 1)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 3)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)


class AWSProvisionStageExistingVpcNoSubnetInfo(AWSProvisionStageTestBase):
    fixture_name = "backend-1-service-1-db"
    env_data_filepath = "environments_aws_ecs_existing_vpc.yml"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 1)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 1)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 1)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 1)
        self.assertEqual(self.resources.get("aws_vpc"), None)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)
        self.assertEqual(len(self.resources["aws_subnet"]), 2)


class AWSProvisionStageExistingVpcCidrsProvided(AWSProvisionStageTestBase):
    fixture_name = "backend-1-service-1-db"
    env_data_filepath = "environments_aws_ecs_existing_vpc_cidrs.yml"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 1)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 1)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 1)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 1)
        self.assertEqual(self.resources.get("aws_vpc"), None)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)
        self.assertEqual(len(self.resources["aws_subnet"]), 2)


class AWSProvisionStageExistingVpcSubnetsProvided(AWSProvisionStageTestBase):
    fixture_name = "backend-1-service-1-db"
    env_data_filepath = "environments_aws_ecs_existing_vpc_subnets.yml"

    def test_tf_is_valid(self):
        self.assertEqual(len(self.resources["aws_db_instance"]), 1)
        self.assertEqual(len(self.resources["aws_db_proxy"]), 1)
        self.assertEqual(len(self.resources["aws_ecs_service"]), 1)
        self.assertEqual(len(self.resources["aws_cloudfront_distribution"]), 1)
        self.assertEqual(len(self.resources["aws_ecr_repository"]), 1)
        self.assertEqual(self.resources.get("aws_vpc"), None)
        self.assertEqual(len(self.resources["aws_acm_certificate"]), 2)
        self.assertEqual(len(self.resources["aws_route53_zone"]), 1)
        self.assertEqual(len(self.resources["aws_subnet"]), 2)
        self.assertEqual(self.resources.get("aws_route_table"), None)
