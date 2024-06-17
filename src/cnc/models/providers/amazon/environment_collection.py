import os
import shutil
import boto3
import json
from cnc.models import EnvironmentCollection
from typing import Literal
from cnc.logger import get_logger

log = get_logger(__name__)


class AWSEnvironmentCollection(EnvironmentCollection):
    provider: Literal["aws"]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def hosted_zone_ns_records(self):
        return self.get_terraform_output("hosted_zone_ns_records")

    @property
    def task_execution_role_arn(self):
        return f"arn:aws:iam::{self.account_id}:role/" f"{self.instance_name}-ecs-task"

    @property
    def existing_vpc_config(self):
        for resource in self.existing_resources:
            if resource.name.lower() == "vpc":
                return resource

    @property
    def vpc_resource_address(self):
        if self.existing_vpc_config:
            return f"data.aws_vpc.{self.instance_name}"

        return f"aws_vpc.{self.instance_name}"

    # ------------------------------
    # Instance methods
    # ------------------------------

    def cli_info_for_environment(self, environment):
        return {
            "name": environment.name,
            "hosted_zone_ns_records": self.get_terraform_output(
                "hosted_zone_ns_records"
            ),
            "domains": environment.domains,
        }

    def preconfigure_infrastructure(
        self,
        should_cleanup=True,
        should_regenerate_config=True,
        args=[],
    ):
        config = self.provision_stage_manager
        is_ok = config.make_ready_for_use(
            should_cleanup=should_cleanup,
            should_regenerate_config=should_regenerate_config,
        )

        results = []
        steps = []

        if not is_ok:
            log.info(f"Cannot init TF for {self}")
            return {"ok": False, "results": results, "steps": steps}

        total_plan_changes = config.plan(save=True, plan_filename="total", args=args)

        if not total_plan_changes:
            log.debug(
                "Did not get any total plan changes! Calling apply and logging..."
            )
            try:
                _ret = config.apply(args=args)
            except Exception as e:
                log.debug(f"Error in calling apply... {e}")
                _ret = {"@message": f"Error: {e}"}
            results.append(_ret)

            log.debug(f"Exiting infra configure step for {self}")
            return {"ok": False, "results": results, "steps": steps}

        if total_plan_changes["status"] == "locked":
            steps.append(total_plan_changes)
            log.warning(
                (
                    "TF is locked (call config.unlock(LOCK_ID) in a toolbox if"
                    f" safe) for {self}: {total_plan_changes}"
                )
            )
            return {"ok": False, "results": results, "steps": steps}

        total_plan_changes["resource_changes"] = {
            "create": [],
            "update": [],
            "delete": [],
        }
        plan_json = config.plan_json(plan_filename="total") or {}
        for rc in plan_json.get("resource_changes", []):
            actions = rc["change"]["actions"]
            resource_data = {key: rc[key] for key in rc.keys() if key not in ["change"]}
            resource_data["actions"] = actions
            if "create" in actions:
                total_plan_changes["resource_changes"]["create"].append(resource_data)
            elif "delete" in actions:
                total_plan_changes["resource_changes"]["delete"].append(resource_data)
            elif "update" in actions:
                total_plan_changes["resource_changes"]["update"].append(resource_data)

        steps.append(total_plan_changes)

        return {"ok": True, "results": results, "steps": steps}

    def configure_infrastructure(
        self,
        should_cleanup=True,
        should_regenerate_config=True,
        args=[],
    ):
        config = self.provision_stage_manager

        if not config.saved_plan_exists(plan_filename="total"):
            res = self.preconfigure_infrastructure(
                should_cleanup=should_cleanup,
                should_regenerate_config=should_regenerate_config,
            )
            if not res["ok"]:
                return res
        else:
            res = {"steps": [], "results": []}
            res["steps"].append(config.plan_json(plan_filename="total"))

        _ret = config.apply(use_saved=True, plan_filename="total", args=args)
        log.debug(f"TF apply output: {_ret}")

        _ok = True
        if _ret.get("@message", "").startswith("Error: "):
            _ok = False

        res["results"].append(_ret)

        config.cleanup()
        return {"ok": _ok, "results": res["results"], "steps": res["steps"]}

    def get_secret_value(self, secret_id, version_id=None):
        secrets_client = boto3.client("secretsmanager")

        inner_json_key = None
        secret_id_parts = secret_id.rstrip(":").split(":")
        if len(secret_id_parts) > 1:
            secret_id, inner_json_key = secret_id_parts

        kwargs = {"SecretId": secret_id}
        if version_id:
            kwargs["VersionId"] = version_id

        secret_string = secrets_client.get_secret_value(**kwargs).get("SecretString")
        if inner_json_key:
            return json.loads(secret_string)[inner_json_key]

        return secret_string

    def generate_tf_assets(self, config_files_path, rendered_files_path):
        log.debug(f"Generating provider assets for {self}...")
        # Zip the js file
        # ensure its in env_collection config_files_path
        zip_file_path = os.path.join(rendered_files_path, "frontend_routing_lambda")
        shutil.make_archive(
            zip_file_path,
            "zip",
            root_dir=(f"{config_files_path}/frontend_routing_lambda"),
        )

        return True
