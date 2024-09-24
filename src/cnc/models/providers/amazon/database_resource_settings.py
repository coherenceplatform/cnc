import re
import json
from typing import Literal

from cnc.models.config.resource import DatabaseResourceSettings
from cnc.logger import get_logger

log = get_logger(__name__)


class AWSDatabaseResourceSettings(DatabaseResourceSettings):
    provider: Literal["aws"]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def managed_secret_id(self):
        return f"{self.environment.instance_name}-secrets"

    @property
    def url_secret_id(self):
        return f"{self.managed_secret_id}:{self.service.instance_name}_url::"

    @property
    def password_secret_id(self):
        return f"{self.managed_secret_id}:{self.service.instance_name}_password::"

    @property
    def database_credentials_secret_id(self):
        if self.use_existing:
            return self.use_existing.secret_id

        return f"{self.service.instance_name}-db-creds"

    @property
    def host_output_tf_value_string(self):
        resource_type_fragment = "${"

        if self.use_db_proxy:
            resource_type_fragment += "aws_db_proxy"
        elif self.use_existing:
            if self.cluster_mode:
                resource_type_fragment += "data.aws_rds_cluster"
            else:
                resource_type_fragment += "data.aws_db_instance"
        else:
            resource_type_fragment += "aws_db_instance"

        return "".join(
            [f"{resource_type_fragment}.", self.service.instance_name, ".endpoint}"]
        )

    @property
    def password_from_db_secret(self):
        try:
            db_secret_value = self.collection.get_secret_value(
                self.database_credentials_secret_id
            )
            return json.loads(db_secret_value).get("password")
        except Exception as e:
            log.debug(f"No existing db secret found for {self.service}: {e}")
            return None

    @property
    def engine_family(self):
        engine_to_family = {
            "mysql": "MYSQL",
            "sqlserver": "SQLSERVER",
            "postgres": "POSTGRESQL",
        }

        return engine_to_family[self.engine.lower()]

    @property
    def identifier(self):
        if self.use_existing:
            return self.service.instance_name

        identifier = re.sub("-+", "-", self.service.instance_name)
        identifier = re.sub("cursor", "cvrsor", identifier)

        return identifier

    @property
    def license_model(self):
        if self.engine.lower() == "sqlserver":
            return "license-included"

    @property
    def instance_class(self):
        if self.engine.lower() == "sqlserver":
            return "db.t3.small"

        return "db.t3.micro"

    @property
    def db_name(self):
        if self.engine.lower() != "sqlserver":
            return super().db_name

    @property
    def cluster_mode(self):
        return bool(self.use_existing and self.use_existing.cluster_mode)

    @property
    def toolbox_ssh_port_mapping(self):
        return (
            "{"
            f'"host":["{self.database_endpoint}"],"portNumber":'
            f'["{self.remote_port}"], "localPortNumber":["{self.local_port}"]'
            "}"
        )
