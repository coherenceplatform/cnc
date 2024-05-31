from typing import Literal
from cnc.models.config.resource import DatabaseResourceSettings
from cnc.logger import get_logger

log = get_logger(__name__)


class GCPDatabaseResourceSettings(DatabaseResourceSettings):
    provider: Literal["gcp"]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def password_secret_id(self):
        return f"{self.service.instance_name}_password"

    @property
    def url_secret_id(self):
        return f"{self.service.instance_name}_url"

    @property
    def host_output_tf_value_string(self):
        tf_resource_type = "google_sql_database_instance."
        host_attr = ".private_ip_address"

        if "lite" in self.application.flavor:
            host_attr = ".public_ip_address"

        if self.use_existing:
            tf_resource_type = f"data.{tf_resource_type}"

        return "".join(
            ["${", tf_resource_type, self.service.instance_name, host_attr, "}"]
        )

    @property
    def password_from_db_secret(self):
        try:
            return self.collection.get_secret_value(self.password_secret_id)
        except Exception as e:
            log.debug(f"No existing db secret found for {self.service}: {e}")
            return None

    @property
    def toolbox_managed_environment_variables(self):
        if "lite" in self.application.flavor:
            _env = self.managed_environment_variables

            db_password = self.database_password
            db_url = self.database_url(db_password=db_password)
            _env.update(
                {
                    f"{self.env_var_base}_DATABASE_URL": db_url,
                    "DATABASE_URL": db_url,
                    f"{self.env_var_base}_DB_PASSWORD": db_password,
                    "DB_PASSWORD": db_password,
                }
            )
            return _env

        return super().toolbox_managed_environment_variables

    @property
    def toolbox_ssh_port_mapping(self):
        return f"{self.local_port}:{self.database_endpoint}:{self.remote_port}"
