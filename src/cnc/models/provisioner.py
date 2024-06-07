import subprocess
import os
import hashlib
import json
import time
import base64
import re

import pygohcl
from .cycle_stage_base import CollectionTemplatedBase

from cnc.logger import get_logger

log = get_logger(__name__)


class ProvisionStageManager(CollectionTemplatedBase):
    template_type = "provision"
    entrypoint_script_name = "main.tf.j2"

    def __init__(self, *args, **kwargs):
        super().__init__(*args)
        self.output_only = kwargs.get("output_only", False)

    @property
    def tf_state_namespace(self):
        return f"{self.collection.cloud_resource_namespace}"

    @property
    def infra_state_hash(self):
        # this is the template, not the rendered TF file
        main_tpl = f"{self.config_files_path}/main.tf.j2"
        if not os.path.isfile(main_tpl):
            log.info(f"{main_tpl} not a file...")
            return ""

        _hash = hashlib.sha256()
        with open(main_tpl) as f:
            _hash.update(f.read().encode())
        template_hash = _hash.hexdigest()

        _hash = hashlib.sha256()
        _state = f"{self.collection.unique_id}:{template_hash}:{self.application.version}:{self.application.flavor}:{self.collection.account_id}:{self.application.name}"
        # log.debug(f"Raw State for {self}: {_state}")
        hashed = hashlib.sha256()
        hashed.update(_state.encode())
        hexdigest = hashed.hexdigest()
        # log.info(f"Digest: {hexdigest}")
        return hexdigest

    def make_ready_for_use(
        self,
        should_cleanup=True,
        should_regenerate_config=True,
    ):
        if should_cleanup:
            log.debug(f"Cleaning up & setting up at start for {self}")

            if not self.cleanup():
                return False

            if not self.setup():
                return False

        if should_regenerate_config:
            log.debug(
                f"Writing {self.application.template_config.provision_filename} for {self}"
            )
            if not self.write_template(
                self.application.template_config.provision_filename
            ):
                return False

        return self.init()

    def template_context(self):
        if self.application.provider_is_aws:
            frontend_names = []
            for svc in self.collection.frontend_services:
                if svc.name not in frontend_names:
                    frontend_names.append(svc.name)

            # this hash is used to prevent tf errors
            # in the event of a major infra change
            # (e.g. switching from a frontend only app to a backend only app)
            #
            # when the hash changes, it forces creation of a new
            # cloudfront dist instead of updating an existing one in place
            fe_hash = base64.b64encode("".join(frontend_names).encode()).decode()
            fe_hash = re.sub("\\W", "", fe_hash)
        else:
            fe_hash = ""

        return {
            "output_only": self.output_only,
            "app": self.application,
            "env_collection": self.collection,
            "config_renderer": self,
            "frontend_hash": fe_hash,
            "svc_path_lambda": lambda svc: len(svc.settings.url_path),
            "sorted": sorted,
            "has_postgres_db": [
                True
                for r in self.collection.database_resources
                if r.settings.engine == "postgres"
            ],
            "has_mysql_db": [
                True
                for r in self.collection.database_resources
                if r.settings.engine == "mysql"
            ],
            "has_mssql_db": [
                True
                for r in self.collection.database_resources
                if "sqlserver" in r.settings.engine
            ],
            "os_env": os.environ,
        }

    def copy_templates(self):
        self.copy_template_dir()

        if not self.output_only:
            self.collection.generate_tf_assets(
                self.config_files_path, self.rendered_files_path
            )

    @property
    def config_files_path(self):
        if self.output_only:
            return (
                f"{self.collection.config_files_path}/output_only/{self.template_type}"
            )

        return f"{self.collection.config_files_path}/{self.template_type}"

    @property
    def is_ready(self):
        return os.path.isdir(f"{self.rendered_files_path}/.terraform")

    def init(self):
        log.debug(f"Installing TF modules/providers for {self}")
        _ret = self._tf_command("init", capture_output=True)
        return self._return_true_if_successful(_ret)

    def unlock(self, lock_id):
        _ret = self._tf_command("force-unlock", [str(lock_id)], options_list=["-force"])
        return self._return_true_if_successful(_ret)

    def saved_plan_exists(self, plan_filename="tfplan"):
        filename = f"{self.rendered_files_path}/{plan_filename}"
        return os.path.isfile(filename)

    def clean_saved_plan(self, plan_filename="tfplan"):
        filename = f"{self.rendered_files_path}/{plan_filename}"
        if self.saved_plan_exists(plan_filename=plan_filename):
            os.remove(filename)

    def plan(self, save=False, plan_filename="tfplan", target=None):
        args = ["-json"]

        if save:
            self.clean_saved_plan(plan_filename)
            args.extend(["-out", plan_filename])
        if target:
            args.extend(["-target", target])

        _ret = self._tf_command("plan", args=args, capture_output=True)

        if not _ret:
            log.info(f"{self} got None in plan")
            return {"status": "not_ready"}

        for _log in _ret.stdout.decode().splitlines():
            try:
                parsed_log = json.loads(_log)
            except Exception:
                log.debug(f"Cannot parse log line from TF ({self}): {_log}")
                continue
            if parsed_log.get("type") == "change_summary":
                parsed_log.update({"status": "ready"})
                return parsed_log
            elif (
                parsed_log.get("@message", "")
                == "Error: Error acquiring the state lock"
            ):
                # this is just so we log the lock ID - would be best to parse it and return in the status dict...
                _ret = self._tf_command("plan", capture_output=True)
                lock_logs = _ret.stderr.decode()
                log.debug(f"{lock_logs}")
                return {"status": "locked", "info": lock_logs}

        log.debug(f"No change summary log available for {self}: \n...")

    def plan_json(self, plan_filename="tfplan"):
        # log.debug(f"Getting plan JSON for {self}: {plan_filename}")
        _ret = self._tf_command("show", ["-json", plan_filename], capture_output=True)

        try:
            return json.loads(_ret.stdout)
        except Exception:
            log.debug(f"Cannot parse plan_json from TF ({self}): {_ret}")
            return {}

    def destroy_item(self, item):
        return self._tf_command("destroy", args=["-auto-approve", "-target", item])

    def destroy(self):
        return self._tf_command("destroy", args=["-auto-approve"], capture_output=True)

    def validate(self):
        _ret = self._tf_command("validate")
        return self._return_true_if_successful(_ret)

    def parse_config_file(self, tfconfig="main.tf"):
        with open(f"{self.rendered_files_path}/{tfconfig}", "r") as f:
            parsed = pygohcl.loads(f.read())
        return parsed

    @property
    def summarized_resource_state(self):
        state = {}
        parsed = self.parse_config_file()

        for resource_type, resources in parsed["resource"].items():
            for address, resource_data in resources.items():
                if resource_type in state:
                    state[resource_type].append({"address": address})
                else:
                    state[resource_type] = [{"address": address}]

        return state

    def apply(self, use_saved=False, plan_filename="tfplan"):
        args = ["-json"]
        if use_saved:
            args.extend([plan_filename])
        _ret = self._tf_command(
            "apply", args=args, options_list=["-auto-approve"], capture_output=True
        )

        if not _ret:
            log.warning(f"_ret is None for {self}")
            return {}

        cloudfront_error = ""
        if _ret.returncode != 0:
            output = _ret.stdout.decode()
            for _line in output.splitlines():
                try:
                    line = json.loads(_line or "{}")
                except Exception:
                    log.info(f"Cannot load TF log line: {_line}")
                    continue

                imported = False
                for stmt in ["Error 1007: Can't create database", "already exists"]:
                    if not imported and stmt in line.get("@message", ""):
                        imported = self.import_existing_resource(line)

                if imported:
                    continue

                line_msg = line.get("@message", "")
                if "Error 400: Billing account" in line_msg:
                    return {"error": "enable_billing"}
                elif re.match(".+cloudfront_distribution.+Creation errored", line_msg):
                    cloudfront_error = f"Error: {line_msg}"
                else:
                    log_noconflict_tf_line(line)

        try:
            parsed_log = json.loads(_ret.stdout.decode().splitlines()[-1])

            if cloudfront_error:
                if parsed_log.get("@message"):
                    parsed_log["@message"] += f" {cloudfront_error}"
                else:
                    parsed_log["@message"] = cloudfront_error

            return parsed_log
        except Exception:
            log.debug(
                f"Cannot parse apply response logs from TF ({self}): {_ret.stdout}"
            )
            return {"error": f"Cannot parse apply response logs: {_ret.stdout}"}

    def import_existing_resource(self, tf_log_line):
        address = tf_log_line.get("diagnostic", {}).get("address")
        if not address:
            log.info(f"No address to import for existing resource: {tf_log_line}")
            return False

        resource_id = None
        if "Error creating Database" in tf_log_line.get("@message", ""):
            if self.collection.is_production:
                log.info(f"Skipping database import for production for {tf_log_line}")
                return False

            db_name = self.parse_database_resource_id(tf_log_line)
            db_instance_name = ""
            for db_resource in self.collection.database_resources:
                if db_resource.instance_name in address:
                    db_instance_name = db_resource.instance_name
                    break

            resource_id = f"{db_instance_name}/{db_name}"

        if not resource_id:
            log.info(f"No resource ID to import for {tf_log_line}")
            return False

        log.info(f"Trying importing {resource_id} to {address}")
        return self.import_resource(address, resource_id)

    def parse_database_resource_id(self, tf_log_line):
        msg = tf_log_line.get("@message", "")

        try:
            return re.search('".+"', msg)[0].replace('"', "")
        except Exception:
            log.info(f"Cannot parse DB name from {msg}")

    def debug(self):
        with open(
            f"{self.rendered_files_path}/{self.application.template_config.provision_filename}",
            "r",
        ) as f:
            print(f.read())

    def import_resource(self, resource_address, resource_id):
        _ret = self._tf_command("import", args=[resource_address, resource_id])
        return self._return_true_if_successful(_ret)

    def list_state(self):
        _ret = self._tf_command("state", args=["list"])
        return self._return_true_if_successful(_ret)

    def clean_state(self, resource_address):
        # TODO: make sure it's a valid address in the list?
        _ret = self._tf_command("state", args=["rm", resource_address])
        return self._return_true_if_successful(_ret)

    def output(self):
        _ret = self._tf_command("output", ["-json"], capture_output=True)
        if _ret and (_ret.returncode == 0):
            return json.loads(_ret.stdout.decode())
        return {}

    def _return_true_if_successful(self, _ret):
        if not _ret:
            return False

        if _ret.returncode == 0:
            return True
        else:
            # self.debug()
            return False

    def _tf_command(self, command, args=None, options_list=None, capture_output=False):
        start = int(time.time())
        if (not self.is_ready) and (command != "init"):
            log.info(f"Cannot {command}|{options_list} - not ready!: {self}")
            if command not in ["init"]:
                return

        full_command = ["terraform", command]

        if options_list and isinstance(options_list, list):
            full_command = full_command + options_list
        if args:
            full_command = full_command + args

        tf_cache_dir = "/tmp/CNC_tfplugin"
        if not os.path.isdir(tf_cache_dir):
            os.mkdir(tf_cache_dir)

        _ret = subprocess.run(
            full_command,
            cwd=self.rendered_files_path,
            capture_output=capture_output,
            env=dict(os.environ, TF_PLUGIN_CACHE_DIR=tf_cache_dir, COLUMNS="1000"),
        )

        end = int(time.time())
        duration = end - start

        log.info(
            f"TF RUN ({self}): [{full_command}] {_ret.returncode} in {duration} seconds"
        )

        if (_ret.returncode != 0) and (command == "init"):
            log.debug(f"dir contents: {os.listdir(self.rendered_files_path)}")
            log.debug(_ret.stdout)
            log.debug(_ret.stderr)
            log.debug("\n\n----------------\n\n")
            # self.debug()
            log.debug("\n\n----------------\n\n")

        return _ret


def log_noconflict_tf_line(line):
    ignore_strings = [
        "Still creating...",
        "Still destroying...",
        "Warning: Applied changes may be incomplete",
        "Destroying...",
        "Plan to delete",
    ]

    for _ in ignore_strings:
        message = line.get("@message", "")
        if (message == "Terraform 1.1.4") or (_ in message):
            return

    log.info(f"TF log: {line}")
