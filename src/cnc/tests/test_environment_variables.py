from unittest.mock import patch

from .base_test_class import CNCBaseTestCase
from cnc.models import Application
from cnc.models.providers.google.environment_collection import GCPEnvironmentCollection

from cnc.logger import get_logger

log = get_logger(__name__)


class EnvironmentVariablesTestCase(CNCBaseTestCase):
    fixture_name = "backend-1-service-1-db-variables-aliases"

    def setUp(self):
        super().setUp()
        app = Application.from_environments_yml("environments.yml")
        self.collection = app.collections[0]
        self.environment = self.collection.environments[0]
        self.assertEqual(self.environment.name, "main")

    def test_variables(self):
        self.assertEqual(len(self.environment.environment_variables), 6)

        _std = self.environment.environment_variables[0]
        self.assertEqual(_std.name, "foo-standard")
        self.assertEqual(_std.value, "bar")
        self.assertEqual(_std.secret_id, None)
        self.assertEqual(_std.output_name, None)
        self.assertEqual(_std.alias, None)

        _secret = self.environment.environment_variables[1]
        with patch.object(
            GCPEnvironmentCollection, "get_secret_value", return_value="secretvalue"
        ) as secret_mock:
            self.assertEqual(_secret.value, "secretvalue")
            secret_mock.assert_called_once

        self.assertEqual(_secret.secret_id, "bar123")
        self.assertEqual(_secret.output_name, None)
        self.assertEqual(_secret.alias, None)

        _std_alias = self.environment.environment_variables[3]
        self.assertEqual(_std_alias.name, "foo-standard-alias")
        self.assertEqual(_std_alias.secret_id, None)
        self.assertEqual(_std_alias.output_name, None)
        self.assertEqual(_std_alias.alias, "foo-standard")
        self.assertEqual(_std.value, "bar")

    def test_items_property(self):
        item_names = [item.name for item in self.environment.environment_items]

        # variable
        self.assertIn("foo-standard", item_names)
        # managed var
        self.assertIn("DB_PASSWORD", item_names)
        # managed secret
        self.assertIn("DB1_ENDPOINT", item_names)

        # check that there are no dupe names
        self.assertEqual(len(item_names), len(set(item_names)))
