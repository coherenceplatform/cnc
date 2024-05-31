from .base_test_class import CNCBaseTestCase
from cnc.models import Application

from cnc.logger import get_logger

log = get_logger(__name__)


class EnvironmentBaseTestCase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml("environments.yml")
        self.collection = app.collections[0]
        self.environment = self.collection.environments[0]
        self.assertEqual(self.environment.name, "main")


class EnvironmentUseExistingDBTestCase(EnvironmentBaseTestCase):
    fixture_name = "backend-1-service-1-db-use-existing"

    def test_environment_use_existing_db(self):
        self.assertEqual(len(self.collection.environments), 1)
        self.assertEqual(self.environment.existing_resources[0].name, "db1")
        self.assertEqual(self.environment.existing_resources[0].instance_name, "foobar")


class EnvironmentBothUseExistingDBTestCase(EnvironmentBaseTestCase):
    fixture_name = "backend-1-service-1-db-both-use-existing"

    def test_environment_use_existing_db(self):
        self.assertEqual(len(self.collection.environments), 1)
        self.assertEqual(self.environment.existing_resources[0].name, "db1")
        self.assertEqual(self.environment.existing_resources[0].instance_name, "bazbar")


class EnvironmentCollectionTwoServicesandDBsTwoEnvsTest(EnvironmentBaseTestCase):
    fixture_name = "backend-1-service-2-db-2-envs"

    def test_environment_domain(self):
        self.assertEqual(len(self.collection.environments), 2)
        self.assertEqual(
            self.environment.domain,
            "main.my-backend-test-app.testnewsite.coherencesites.com",
        )

    def test_environment_services(self):
        self.assertEqual(len(self.environment.services), 3)
        self.assertEqual(len(self.environment.web_services), 1)
