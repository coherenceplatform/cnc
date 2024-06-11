import os
import hashlib
import re
import urllib
import secrets
from typing import List, Optional, Literal, Union
from pydantic import Field

from ..base_model import BaseModel, IgnoredType

from cnc.logger import get_logger

log = get_logger(__name__)


STARTING_PORTS = {
    "POSTGRES": 5432,
    "REDIS": 6379,
    "MYSQL": 3306,
    "SQLSERVER-EX": 1433,
    "SQLSERVER-WEB": 1433,
}


class BaseResourceSettings(BaseModel):
    type: str
    raw_use_existing: Optional[List[dict]] = Field(
        default_factory=list, alias="use_existing"
    )
    engine: Optional[str] = None
    provider: str

    # ------------------------------
    # Parent relationships
    # ------------------------------
    config: Optional[IgnoredType] = IgnoredType()
    service: Optional[IgnoredType] = IgnoredType()

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def toolbox_resource_host(self):
        return os.environ.get("CNC_TOOLBOX_RESOURCE_HOST", "localhost")

    @property
    def collection(self):
        return self.service.environment.collection

    @property
    def application(self):
        return self.service.environment.application

    @property
    def environment(self):
        return self.service.environment

    @property
    def is_resource(self):
        return True

    @property
    def host_output_id(self):
        return f"{self.type}_host_{self.environment.name}_{self.service.instance_name}"

    @property
    def env_var_base(self):
        return f"{self.service.name}".upper().replace("-", "_")

    @property
    def is_web(self):
        return False

    @property
    def is_cache(self):
        return self.type == "cache"

    @property
    def is_filesystem(self):
        return self.type == "filesystem"

    @property
    def is_object_storage(self):
        return self.type == "object_storage"

    @property
    def is_message_queue(self):
        return self.type == "message_queue"

    @property
    def is_database(self):
        return self.type == "database"

    @property
    def unique_id(self):
        hash_str = (
            f"{self.config.environment.application.name}:"
            f"{self.config.environment.collection.name}:"
            f"{self.service.name}:{self.engine}"
        )
        _hash = hashlib.sha256()
        _hash.update(hash_str.encode())
        return _hash.hexdigest()

    @property
    def common_managed_environment_variables(self):
        return {}

    @property
    def use_existing(self):
        return

    @property
    def managed_secret_values_for_tf(self):
        log.warning(f"managed_secret_values_for_tf not defined for {self}")
        return {}

    @property
    def managed_environment_secrets(self):
        return {}

    # ------------------------------
    # Instance methods
    # ------------------------------
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.service.name} ({self.type})>"

    __str__ = __repr__


class DatabaseResourceSettings(BaseResourceSettings):
    type: Literal["database"]
    engine: Optional[str] = "postgres"
    snapshot_file_path: Optional[str] = ""
    snapshot_type: Optional[str] = "data"
    raw_adapter: Optional[str] = Field(
        alias="adapter",
        default=None,
    )
    use_db_proxy: Optional[bool] = True
    version: Union[str, int, float]

    # ------------------------------
    # Properties
    # ------------------------------

    @property
    def use_existing(self):
        for entry in self.service.environment.existing_resources:
            if entry.name == self.service.name:
                return entry

    @property
    def existing_instance_name(self):
        if self.use_existing:
            return self.use_existing.instance_name

    @property
    def manage_databases(self):
        if self.use_existing:
            return self.use_existing.manage_databases
        return True

    @property
    def database_endpoint(self):
        return self.collection.get_terraform_output(self.host_output_id) or "localhost"

    @property
    def db_name(self):
        if self.use_existing and self.use_existing.db_name:
            return self.use_existing.db_name

        if self.service.environment.application.provider_is_aws:
            dbname = self.service.environment.name.replace("-", "_")
            if re.match("^\\d", dbname):
                return f"db{dbname}"
            else:
                return dbname
        else:
            return self.service.environment.name.lower()

    @property
    def username(self):
        if self.use_existing and self.use_existing.username:
            return self.use_existing.username

        # AWS doesn't like dashes in DB usernames for RDS
        # this is safer across all providers
        return self.service.environment.application.name.replace("-", "_")

    @property
    def connection_string_adapter(self):
        return self.raw_adapter or self.engine.lower()

    @property
    def minor_version_specified(self):
        return bool(isinstance(self.version, float) or float(self.version) % 1)

    @property
    def snapshot_filename(self):
        if self.snapshot_file_path:
            _full = self.snapshot_file_path
            return _full.split("/")[-1]
        return ""

    @property
    def snapshot_bucket_name(self):
        if self.snapshot_file_path:
            _full = self.snapshot_file_path
            return _full.split("/")[0]
        return ""

    @property
    def load_database_snapshot(self):
        if self.snapshot_file_path:
            return True
        return False

    @property
    def managed_environment_variables(self):
        _env = self.common_managed_environment_variables

        _env.update(
            {
                f"{self.env_var_base}_IP": self.database_endpoint,
                f"{self.env_var_base}_HOST": self.database_endpoint,
                f"{self.env_var_base}_ENDPOINT": self.database_endpoint,
                f"{self.env_var_base}_PORT": str(STARTING_PORTS[self.engine.upper()]),
                "DB_NAME": self.db_name,
                "DB_USER": self.username,
                "DB_ENGINE": self.engine.lower(),
            }
        )

        if self.snapshot_file_path:
            _env["SNAPSHOT_FILE_PATH"] = self.snapshot_file_path
            _env["SNAPSHOT_FILE_NAME"] = self.snapshot_filename

        return _env

    @property
    def toolbox_managed_environment_variables(self):
        _env = self.common_managed_environment_variables

        db_password = self.database_password
        db_url = self.database_url(db_password=db_password, toolbox=True)
        _env.update(
            {
                f"{self.env_var_base}_ENDPOINT": self.toolbox_resource_host,
                f"{self.env_var_base}_HOST": self.toolbox_resource_host,
                f"{self.env_var_base}_IP": self.toolbox_resource_host,
                f"{self.env_var_base}_PORT": self.local_port,
                "DB_NAME": self.db_name,
                "DB_USER": self.username,
                "DB_ENGINE": self.engine.lower(),
                f"{self.env_var_base}_DATABASE_URL": db_url,
                "DATABASE_URL": db_url,
                f"{self.env_var_base}_DB_PASSWORD": db_password,
                "DB_PASSWORD": db_password,
            }
        )

        if self.snapshot_file_path:
            _env["SNAPSHOT_FILE_PATH"] = self.snapshot_file_path
            _env["SNAPSHOT_FILE_NAME"] = self.snapshot_filename

        return _env

    @property
    def cloud_resource_version(self):
        # see https://cloud.google.com/sql/docs/mysql/admin-api/rest/v1beta4/SqlDatabaseVersion
        if self.engine in ["postgres", "mysql"]:
            return f'{self.engine.upper()}_{str(self.version).replace(".", "_")}'

    @property
    def managed_environment_secrets(self):
        return {
            f"{self.env_var_base}_DB_PASSWORD": self.password_secret_id,
            "DB_PASSWORD": self.password_secret_id,
            f"{self.env_var_base}_DATABASE_URL": self.url_secret_id,
            "DATABASE_URL": self.url_secret_id,
        }

    @property
    def managed_secret_values_for_tf(self):
        db_url = self.database_url(self.database_password)
        if "@localhost" in db_url:
            db_url_p1, db_url_p2 = db_url.split("@localhost")
            db_url = f"{db_url_p1}@{self.host_output_tf_value_string}{db_url_p2}"

        return {
            self.url_secret_id.replace("::", "").split(":")[-1]: db_url,
            self.password_secret_id.replace("::", "").split(":")[
                -1
            ]: self.database_password,
        }

    @property
    def database_password(self):
        if not hasattr(self, "_database_password"):
            if self.environment.database_password:
                self._database_password = self.environment.database_password.value
            else:
                self._database_password = (
                    self.password_from_db_secret or secrets.token_hex()[:39]
                )

        return self._database_password

    @property
    def remote_port(self):
        return STARTING_PORTS[self.engine.upper()]

    @property
    def local_port(self):
        starting_port = STARTING_PORTS[self.engine.upper()] + 10
        for i, resource in enumerate(self.environment.database_resources):
            if self.service.instance_name == resource.instance_name:
                return str(starting_port + i)

    # ------------------------------
    # Instance methods
    # ------------------------------

    def database_url(self, db_password="password", toolbox=False):
        if toolbox:
            db_port = self.local_port
            db_endpoint = self.toolbox_resource_host
        else:
            db_port = STARTING_PORTS[self.engine.upper()]
            db_endpoint = self.database_endpoint

        db_url_params = {}
        # SSL is enabled by default for postgres >= 15
        if not self.engine.lower() == "postgres" or int(self.version) < 15:
            db_url_params["sslmode"] = "disable"

        environment = self.service.environment
        if environment.application.provider_is_aws:
            try:
                enc_db_pw = urllib.parse.quote(db_password)
            except Exception as e:
                log.warn(f"Unable to encode db pw for {self.service} | {e}")
                enc_db_pw = db_password

            db_url = (
                f"{self.connection_string_adapter}://{self.username}:"
                f"{enc_db_pw}@{db_endpoint}:{db_port}/{self.db_name}"
            )

            if db_url_params:
                db_url += f"?{urllib.parse.urlencode(db_url_params, safe='/:')}"

            return db_url
        elif environment.application.provider_is_gcp:
            try:
                enc_db_pw = urllib.parse.quote(db_password)
            except Exception as e:
                log.warn(f"Unable to encode db pw for {self.service} | {e}")
                enc_db_pw = db_password

            db_url = (
                f"{self.connection_string_adapter}://{self.username}"
                f":{enc_db_pw}@{db_endpoint}:{db_port}/{self.db_name}"
            )

            if db_url_params:
                db_url += f"?{urllib.parse.urlencode(db_url_params, safe='/:')}"

            return db_url


class CORSSettings(BaseModel):
    allowed_methods: List[str]
    allowed_origins: List[str]


class CustomBucketHeader(BaseModel):
    name: str
    value: str
    type: Optional[str] = "response"


class BucketResourceSettings(BaseResourceSettings):
    type: Literal["object_storage"]
    cors: Optional[List[CORSSettings]] = []
    custom_headers: Optional[List[CustomBucketHeader]] = []

    @property
    def custom_response_headers(self):
        headers = []
        for header in self.custom_headers:
            if header.type == "response":
                headers.append(header)

        return headers

    @property
    def custom_request_headers(self):
        headers = []
        for header in self.custom_headers:
            if header.type == "request":
                headers.append(header)

        return headers

    @property
    def managed_environment_variables(self):
        _env = {}

        # TODO: make foo real output for bucket name
        _env.update(
            {
                f"{self.service.name.upper()}_URL": self.collection.get_terraform_output(
                    "foo"
                )
                or self.bucket_name,
                f"{self.service.name.upper()}_NAME": self.bucket_name,
            }
        )

        return _env

    @property
    def bucket_name(self):
        if self.use_existing:
            return self.use_existing.instance_name

        name = f"{self.service.name}-{self.config.environment.name}"
        _hash = hashlib.sha256()
        _hash.update(name.encode())
        full_name = (
            f"{self.service.name}-{self.config.environment.name}"
            f"-{_hash.hexdigest()}"
        ).replace("_", "-")[:62]
        # first and last chars must be letters/digits
        first_char = full_name[0]
        if not (first_char.isalpha() or first_char.isdigit()):
            full_name = "b" + full_name[1:]

        last_char = full_name[-1]
        if not (last_char.isalpha() or last_char.isdigit()):
            full_name = full_name[:61] + "b"
        return full_name


class FilesystemResourceSettings(BaseResourceSettings):
    type: Literal["filesystem"]
    mountpoint: Optional[str] = None

    @property
    def existing_filesystem_id(self):
        if self.use_existing and self.is_filesystem:
            if self.service.environment.project_type == self.use_existing.project_type:
                return self.use_existing.instance_name

    @property
    def existing_filesystem_mountpoint(self):
        if self.use_existing and self.is_filesystem:
            if self.service.environment.project_type == self.use_existing.project_type:
                return self.mountpoint or self.use_existing.instance_name


class QueueResourceSettings(BaseResourceSettings):
    type: Literal["message_queue"]
    fifo: Optional[bool] = True

    @property
    def managed_environment_variables(self):
        _env = self.common_managed_environment_variables
        # TODO: this wont work - need to make sure url is set properly here
        _env.update(
            {
                f"{self.name.upper()}_URL": self.service.environment.data.get(
                    f"sqs_queue_{self.queue_name}"
                ),
                f"{self.name.upper()}_NAME": self.queue_name,
            }
        )
        return _env

    @property
    def use_existing(self):
        for entry in self.service.environment.existing_resources:
            if entry.name == self.service.name:
                return entry

    @property
    def tf_safe_queue_name(self):
        # cannot include .fifo at the end
        return self.queue_name.replace(".fifo", "")

    @property
    def queue_name(self):
        # Queue names must be unique for your AWS account and region
        # must be made up of only uppercase and lowercase ASCII letters,
        # numbers, underscores, and hyphens, and must be between 1 and 80 characters long.
        # For a FIFO (first-in-first-out) queue, the name must end with the .fifo suffix.
        if self.use_existing and self.use_existing.instance_name:
            return self.use_existing.instance_name

        queue_name = f"{self.environment.instance_name[:37]}-{self.name[-37:]}"
        if self.is_fifo:
            queue_name += ".fifo"

        return queue_name


class CacheResourceSettings(BaseResourceSettings):
    type: Literal["cache"]
    engine: Optional[str] = "redis"
    version: Union[str, int, float] = "6"

    @property
    def redis_ip_output_id(self):
        return f"redis_ip_{self.service.instance_name}"

    @property
    def redis_port_output_id(self):
        return f"redis_port_{self.service.instance_name}"

    @property
    def redis_ip(self):
        return (
            self.collection.get_terraform_output(self.redis_ip_output_id) or "localhost"
        )

    @property
    def redis_port(self):
        return str(
            self.collection.get_terraform_output(self.redis_port_output_id)
            or STARTING_PORTS[self.engine.upper()]
        )

    @property
    def managed_environment_variables(self):
        _env = self.common_managed_environment_variables
        _env.update(
            {
                f"{self.env_var_base}_PORT": self.redis_port,
                f"{self.env_var_base}_IP": self.redis_ip,
                f"{self.env_var_base}_HOST": self.redis_ip,
                f"{self.env_var_base}_URL": f"redis://{self.redis_ip}:{self.redis_port}",
                "REDIS_URL": f"redis://{self.redis_ip}:{self.redis_port}",
            }
        )
        return _env

    @property
    def toolbox_managed_environment_variables(self):
        _env = self.common_managed_environment_variables
        _env.update(
            {
                f"{self.env_var_base}_PORT": self.local_port,
                f"{self.env_var_base}_HOST": self.toolbox_resource_host,
                f"{self.env_var_base}_IP": self.toolbox_resource_host,
                f"{self.env_var_base}_URL": (
                    f"redis://{self.toolbox_resource_host}:{self.local_port}"
                ),
                "REDIS_URL": (
                    f"redis://{self.toolbox_resource_host}:{self.local_port}"
                ),
            }
        )
        return _env

    @property
    def is_cache(self):
        return True

    @property
    def local_port(self):
        starting_port = STARTING_PORTS[self.engine.upper()]
        for i, resource in enumerate(self.environment.cache_resources):
            if self.service.instance_name == resource.instance_name:
                return str(starting_port + i)
