from typing import Optional
from google.cloud import secretmanager

from cnc.models import EnvironmentCollection
from typing import Literal

from cnc.logger import get_logger

log = get_logger(__name__)


class GCPEnvironmentCollection(EnvironmentCollection):
    provider: Literal["gcp"]
    allow_net_admin: Optional[bool] = False

    def get_secret_value(self, secret_id, version_id="latest"):
        """
        Access a secret version in Secret Manager.

        Args:
        secret_id: ID of the secret you want to access.
        version_id: Version of the secret; defaults to "latest".

        Returns:
        The secret value as a string.
        """
        # Create the Secret Manager client.
        client = secretmanager.SecretManagerServiceClient()

        # Build the resource name of the secret version.
        name = f"projects/{self.account_id}/secrets/{secret_id}/versions/{version_id}"

        # Access the secret version.
        response = client.access_secret_version(request={"name": name})

        # Return the decoded payload.
        return response.payload.data.decode("UTF-8")

    @property
    def bastion_instance_type(self):
        if self.region == "southamerica-west1":
            return "e2-micro"
        else:
            return "f1-micro"

    @property
    def has_service_domains(self):
        if self.application.flavor == "run-lite":
            return True
        return False

    def cli_info_for_environment(self, environment):
        return {
            "name": environment.name,
            "load_balancer_ip": self.get_terraform_output("load_balancer_ip"),
            "domains": environment.domains,
        }

    def preconfigure_infrastructure(
        self,
        should_cleanup=True,
        should_regenerate_config=True,
    ):
        config = self.provision_stage_manager
        config.make_ready_for_use(
            should_cleanup=should_cleanup,
            should_regenerate_config=should_regenerate_config,
        )

        results = []
        steps = []

        total_plan_changes = config.plan(save=True, plan_filename="total_1")
        if not total_plan_changes:
            log.debug(
                "Did not get any total plan changes! Calling apply and logging..."
            )
            try:
                _ret = config.apply()
            except Exception as e:
                log.debug(f"Error in calling apply... {e}")
                _ret = {"@message": f"Error: {e}"}
            results.append(_ret)

            log.debug(f"Exiting infra configure step for {self}")
            return {"ok": False, "results": results, "steps": steps}

        # eventually we should wrap this with our own lock, then it would be safe to force unlock and proceed...
        if total_plan_changes["status"] == "locked":
            steps.append(total_plan_changes)
            return {"ok": False, "results": results, "steps": steps}

        plan_json = config.plan_json(plan_filename="total_1") or {}
        total_plan_changes["resource_changes"] = {
            "create": [],
            "update": [],
            "delete": [],
        }
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
    ):
        can_configure = True
        config = self.provision_stage_manager

        results = []
        steps = []

        if not config.saved_plan_exists(plan_filename="total_1"):
            res = self.preconfigure_infrastructure(
                should_cleanup=should_cleanup,
                should_regenerate_config=should_regenerate_config,
            )
            if not res["ok"]:
                return res

        total_plan_json = config.plan_json(plan_filename="total_1") or {}
        all_changes = total_plan_json.get("resource_changes", [])

        if self.contains_db_replacement_changes(plan_json=total_plan_json):
            self.process_db_replacement_alert()
            return {"ok": False, "results": results, "steps": steps}

        _ok = False
        ret = config.apply(use_saved=True, plan_filename="total_1")
        if ret and ret.get("error"):
            results.append(ret)
            if ret["error"] == "enable_billing":
                log.info("Cannot proceed with infra config, need billing account!")
                can_configure = False

        seen_url_addresses = []
        if can_configure:
            for change in all_changes:
                if (change["type"] == "google_compute_backend_service") and (
                    ("delete" in change["change"]["actions"])
                    or ("create" in change["change"]["actions"])
                ):
                    # log.debug(
                    #     f"Detected backend service/url map change for {self}, targeting url map and https proxy before continuting"
                    # )

                    if change["address"] in seen_url_addresses:
                        log.debug(f"Skipping {change}")
                        continue
                    else:
                        seen_url_addresses.append(change["address"])

                    # log.debug(f"Processing {change}")

                    url_map_changes = config.plan(
                        save=True, target=change["address"], plan_filename="urlmap"
                    )
                    url_map_changes["change"] = change

                    # log.info(f"Going to apply URL map changes: {url_map_changes}")
                    config.apply(use_saved=True, plan_filename="urlmap")

                if (change["type"] == "google_compute_target_https_proxy") and (
                    change["change"]["actions"] != ["no-op"]
                ):

                    https_proxy_changes = config.plan(
                        save=True,
                        target=f"google_compute_target_https_proxy.{self.instance_name}",
                        plan_filename="httpsproxy",
                    )
                    https_proxy_changes["change"] = change

                    # log.info(f"Going to apply HTTPS proxy changes: {https_proxy_changes}")
                    config.apply(use_saved=True, plan_filename="httpsproxy")

            services_to_cleanup = []
            for change in total_plan_json["resource_changes"]:
                if (
                    (change["type"] == "google_compute_backend_service")
                    and ("delete" in change["change"]["actions"])
                    and (len(change["change"]["actions"]) == 1)
                ) or (
                    (change["type"] == "google_compute_backend_bucket")
                    and ("delete" in change["change"]["actions"])
                    and (len(change["change"]["actions"]) == 1)
                ):
                    # log.debug(
                    #     f"Got stale backend that will need to be cleaned up: {change['address']}"
                    # )
                    services_to_cleanup.append(change["address"])

            total_plan_changes = config.plan(save=True, plan_filename="total")
            total_plan_json = config.plan_json(plan_filename="total") or {}
            if self.contains_db_replacement_changes(plan_json=total_plan_json):
                self.process_db_replacement_alert()
                return {"ok": False, "results": results, "steps": steps}

            log.info(f"Going to apply total plan changes: {total_plan_changes}")
            config.apply(use_saved=True, plan_filename="total")

            addresses_to_clean = []
            for i, service_address in enumerate(services_to_cleanup):
                if service_address in addresses_to_clean:
                    continue
                else:
                    addresses_to_clean.append(service_address)

                # log.debug(f"Cleaning up stale service for {service_address}")
                config.plan(
                    save=True,
                    target=service_address,
                    plan_filename=f"serviceaddress-{i}",
                )
                config.apply(use_saved=True, plan_filename=f"serviceaddress-{i}")
                # log.debug(f"All set cleaning up...")

            # One last apply to properly report success/fail
            _ret = config.apply()

            _ok = True
            if _ret.get("@message", "").startswith("Error: "):
                _ok = False

            results.append(_ret)

            # outputs = config.output()

            config.cleanup()

        return {"ok": _ok, "results": results, "steps": steps}

    def contains_db_replacement_changes(self, plan_json):
        db_resource_types = ["google_sql_database_instance", "google_sql_database"]
        try:
            all_changes = plan_json.get("resource_changes", [])
            for change in all_changes:
                if (
                    change["type"] in db_resource_types
                    and ("delete" in change["change"]["actions"])
                    and ("create" in change["change"]["actions"])
                ):
                    return True
        except Exception as e:
            log.debug(f"Error while checking for db replacement changes: {e}")

        return False

    def process_db_replacement_alert(self):
        """
        Adds an error to configuration results and sends an
        internal slack notification
        """
        self.results.append(
            {
                "@message": "Error: Unsafe operation - Planned database resource replacement detected."
            }
        )

    @property
    def service_identity_email(self):
        return (
            f"{self.cloud_resource_namespace}@{self.account_id}.iam.gserviceaccount.com"
        )
