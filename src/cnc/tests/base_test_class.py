import unittest
import os
import shutil
import uuid


class CNCBaseTestCase(unittest.TestCase):
    fixture_name = ""
    env_data_filepath = "environments.yml"

    def setUp(self):
        if not self.fixture_name:
            raise ValueError("Must provide fixture_name")

        self.working_dir = f"/tmp/{str(uuid.uuid4())}"

        shared_template_dir = f"{os.path.dirname(__file__)}/fixtures/shared"
        fixtures_path = f"{os.path.dirname(__file__)}/fixtures/{self.fixture_name}"

        shutil.copytree(
            shared_template_dir,
            self.working_dir,
            dirs_exist_ok=True,
        )

        shutil.copytree(
            fixtures_path,
            self.working_dir,
            dirs_exist_ok=True,
        )

        # print(f"\n{self.working_dir}")
        # subprocess.run(["ls", "-al", self.working_dir])
        os.chdir(self.working_dir)
        # subprocess.run(["cat", "cnc.yml"])
        # print("\n")

    def tearDown(self):
        shutil.rmtree(
            self.working_dir,
            ignore_errors=True,
        )
