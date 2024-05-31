from .base_test_class import CNCBaseTestCase
from cnc.models import Application

from cnc.logger import get_logger

log = get_logger(__name__)


class EnvironmentCollectionBaseTestCase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"
    env_data_filepath = "environments.yml"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml(self.env_data_filepath)
        self.collection = app.collections[0]


class EnvironmentCollectionTestCase(EnvironmentCollectionBaseTestCase):
    def test_collection_env_by_name(self):
        self.assertIsNone(self.collection.environment_by_name("foo"))
        self.assertIsNotNone(self.collection.environment_by_name("main"))


class EnvironmentCollectionExistingDBTestCase(EnvironmentCollectionBaseTestCase):
    fixture_name = "backend-1-service-1-db-use-existing"

    def test_collection_use_existing_db(self):
        self.assertEqual(
            self.collection.environments[0].existing_resources[0].name, "db1"
        )
        self.assertEqual(
            self.collection.environments[0].existing_resources[0].instance_name,
            "foobar",
        )


class EnvironmentCollectionTwoServicesandDBsTwoEnvsTest(
    EnvironmentCollectionBaseTestCase
):
    fixture_name = "backend-1-service-2-db-2-envs"

    def test_environment_order(self):
        self.assertEqual(len(self.collection.environments), 2)
        self.assertEqual(self.collection.environments[0].name, "main")
        self.assertEqual(self.collection.environments[1].name, "staging")

    def test_environment_services(self):
        self.assertEqual(len(self.collection.all_services), 6)
        self.assertEqual(len(self.collection.all_services_for_type("backend")), 2)
        self.assertEqual(len(self.collection.all_services_for_type("database")), 4)
        self.assertEqual(len(self.collection.all_services_for_type("frontend")), 0)
        self.assertEqual(len(self.collection.all_services_for_type("cache")), 0)


class EnvironmentCollectionRegionSettings(EnvironmentCollectionBaseTestCase):
    fixture_name = "backend-1-service-2-db-2-envs"
    env_data_filepath = "environments_gcp_run_region_settings.yml"

    def test_region_settings(self):
        self.assertEqual(self.collection.region, self.collection.collection_region)
        self.assertEqual(self.collection.region, "us-west2")
        self.assertEqual(self.collection.application.region, "us-east1")
