import re
import string
from typing import (
    List,
    Optional,
    Dict,
    Any,
    Union,
    Annotated,
)
from pydantic import (
    field_validator,
    Field,
    model_validator,
    ValidationInfo,
)
from jinja2 import Template

from cnc.constants import EnvironmentVariableTypes
from cnc.utils import clean_name_string
from ..base_model import BaseModel, IgnoredType
from .resource import BucketResourceSettings
from .settings import (
    FrontendServiceSettings,
    BackendServiceSettings,
    ProviderDeployResourceLimits,
)
from cnc.models.providers.amazon import (
    AWSDatabaseResourceSettings,
    AWSCacheResourceSettings,
)
from cnc.models.providers.google import (
    GCPDatabaseResourceSettings,
    GCPCacheResourceSettings,
)
from cnc.models.toolbox import ToolboxManager

from cnc.logger import get_logger

log = get_logger(__name__)


class BuildSettings(BaseModel):
    raw_dockerfile: Optional[str] = Field(alias="dockerfile", default=None)
    context: Optional[str] = "."

    @property
    def dockerfile(self):
        return f"{self.context}/{self.raw_dockerfile or 'Dockerfile'}"

    @property
    def dockerfile_is_default(self):
        return not self.raw_dockerfile


class DeployResources(BaseModel):
    limits: Optional[ProviderDeployResourceLimits] = Field(
        default_factory=ProviderDeployResourceLimits,
    )

    # ------------------------------
    # Validators
    # ------------------------------

    @model_validator(mode="before")
    def ensure_limits_provider(cls, data, info):
        if not data.get("limits"):
            data["limits"] = {}

        data["limits"]["provider"] = info.context.get("provider")

        return data


class DeploySettings(BaseModel):
    resources: Optional[DeployResources] = Field(default_factory=DeployResources)
    replicas: Optional[int] = 1

    @model_validator(mode="before")
    def ensure_deploy_resources_context(cls, data):
        # This is meant to ensure that validation
        # context is passed to child models
        if not data.get("resources"):
            data["resources"] = {}

        return data


ProviderDatabaseResourceSettings = Annotated[
    Union[GCPDatabaseResourceSettings, AWSDatabaseResourceSettings],
    Field(discriminator="provider"),
]

ProviderCacheResourceSettings = Annotated[
    Union[GCPCacheResourceSettings, AWSCacheResourceSettings],
    Field(discriminator="provider"),
]


class Service(BaseModel):
    name: str
    settings: Union[
        ProviderDatabaseResourceSettings,
        ProviderCacheResourceSettings,
        BucketResourceSettings,
        FrontendServiceSettings,
        BackendServiceSettings,
    ] = Field(alias="x-cnc", discriminator="type")
    build: Optional[BuildSettings] = None
    deploy: DeploySettings
    image: Optional[str] = None
    compose_environment: Dict[str, str] = Field(
        default_factory=dict, alias="environment"
    )
    command: List[str] = Field(default_factory=list)
    ports: Optional[List[str]] = []

    # ------------------------------
    # Parent relationships
    # ------------------------------
    config: Optional[IgnoredType] = IgnoredType()
    environment: Optional[IgnoredType] = Field(
        default_factory=IgnoredType,
        alias="env_parent_rel",
    )

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="before")
    def ensure_settings_provider(cls, data, info):
        settings_key = "x-cnc"
        if data.get("x-cnc"):
            settings_key = "x-cnc"
        elif data.get("settings"):
            settings_key = "settings"
        else:
            data[settings_key] = {}

        data[settings_key]["provider"] = info.context.get("provider")

        return data

    @model_validator(mode="before")
    def ensure_deploy_settings_context(cls, data):
        # This is meant to ensure that validation
        # context is passed to child models
        if not data.get("deploy"):
            data["deploy"] = {}

        return data

    @model_validator(mode="after")
    def annotate_children(self):
        self.settings.service = self

        return self

    @field_validator("command", mode="before")
    def validate_command(cls, value: Any) -> list[str]:
        if isinstance(value, str):
            return value.split()
        return value

    @model_validator(mode="before")
    @classmethod
    def default_build_if_no_image(cls, data: dict, info: ValidationInfo):
        if not (data.get("image") or data.get("build")):
            data["build"] = {}

        return data

    # @field_validator("compose_environment", mode="before")
    # def validate_compose_env(cls, value):
    #     if isinstance(value, list):
    #         value = key_equal_value_to_dict(value)
    # pydantic v2 will not "convert" values to strings
    # also need to do something like this for missing values:
    # - value missing
    # - try to get it from os.environ
    # - if not available ignore item entirely
    # return {k: str(v) for k, v in value.items()}

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def port(self):
        if self.ports:
            return self.ports[0].split(":")[-1]

        return "8080"

    @property
    def instance_name(self):
        if (
            hasattr(self.settings, "existing_instance_name")
            and self.settings.existing_instance_name
        ):
            return self.settings.existing_instance_name

        _name = (
            f"{self.settings.unique_id[:10]}-{self.application.name[:5]}-"
            f"{self.environment.collection.name[-5:]}-"
            f"{self.environment.name[-7:]}-{self.name[-7:]}"
        )

        clean = clean_name_string(_name, truncate_len=39)

        # instance names in gcp often have to start with a letter...
        if clean[0].lower() not in string.ascii_lowercase:
            clean = "c" + clean[1:]

        return re.sub("[\\W_]+$", "", clean)

    @property
    def workload_identity_pool(self):
        return f"serviceAccount:{self.environment.collection.account_id}.svc.id.goog[{self.instance_name}/{self.instance_name}]"

    @property
    def is_internal(self):
        return self.settings.internal is True

    @property
    def is_backend(self):
        return self.settings.type == "backend"

    @property
    def is_frontend(self):
        return self.settings.type == "frontend"

    @property
    def is_database(self):
        return self.settings.type == "database"

    @property
    def is_cache(self):
        return self.settings.type == "cache"

    @property
    def is_message_queue(self):
        return self.settings.type == "message_queue"

    @property
    def is_object_storage(self):
        return self.settings.type == "object_storage"

    @property
    def is_filesystem(self):
        return self.settings.type == "filesystem"

    @property
    def included_build_globs(self):
        if self.build.context == ".":
            # match everything
            default_globs = ["**/*"]
            _glob_tmpl = "{_}"
        else:
            default_globs = [f"{self.build.context}/**/*"]
            _glob_tmpl = "{self.build.context}/{_}"

        return [
            _glob_tmpl.format(_=_, self=self)
            for _ in self.settings.build_config.included_paths
        ] or default_globs

    @property
    def excluded_build_globs(self):
        if self.settings.repo_path == ".":
            _glob_tmpl = "{_}"
        else:
            _glob_tmpl = "{self.settings.repo_path}/{_}"

        return [
            _glob_tmpl.format(_=_, self=self)
            for _ in self.settings.build_config.excluded_paths
        ]

    @property
    def environment_outputs(self):
        # aliases are included by the filtered_environment_items method
        return self.filtered_environment_items(
            variable_type=EnvironmentVariableTypes.VARIABLE_TYPE_OUTPUT
        )

    @property
    def environment_secrets(self):
        # aliases are included by the filtered_environment_items method
        return self.config.managed_environment_secrets_for_service(
            service=self
        ) + self.filtered_environment_items(
            variable_type=EnvironmentVariableTypes.VARIABLE_TYPE_SECRET
        )

    @property
    def environment_variables(self):
        # aliases are included by the filtered_environment_items method
        return self.config.managed_environment_variables_for_service(
            service=self
        ) + self.filtered_environment_items(
            variable_type=EnvironmentVariableTypes.VARIABLE_TYPE_STANDARD
        )

    @property
    def environment_items(self):
        # includes all 3 types
        return (
            self.environment_outputs
            + self.environment_secrets
            + self.environment_variables
        )

    @property
    def insecure_environment_items(self):
        # this does not include secrets, meant for deploy runtime config
        # e.g. ECS/cloud run, includes standard/outputs
        return self.environment_variables + self.environment_outputs

    @property
    def gcr_image_name(self):
        app_name = clean_name_string(self.config.environment.application.name, 12)
        service_name = clean_name_string(self.name, 15)
        return f"{app_name}-{service_name}"

    @property
    def domain(self):
        # TODO: figure out how to offer subdomain routing here
        # TODO: do custom domains need to live here if so?
        if self.environment.collection.has_service_domains:
            return self.environment.collection.get_terraform_output(
                f"{self.instance_name}_cloud_run_url"
            )

    @property
    def provider_links(self):
        metadata = self.environment.collection.application.flavor_metadata
        _templates = metadata.get("provider_links_templates", {})

        context = {"service": self}
        _links = [
            {
                "url": Template(_templates.get(self.settings.type, "")).render(context),
                "label": self.settings.type,
            }
        ]

        for worker in self.settings.workers:
            _context = context.copy()
            _context.update(
                {
                    "worker": worker,
                }
            )
            _links.append(
                {
                    "url": Template(_templates.get("worker", "")).render(_context),
                    "label": worker.name,
                    "type": "worker",
                }
            )

        for task in self.settings.scheduled_tasks:
            _context = context.copy()
            _context.update(
                {
                    "task": task,
                }
            )
            _links.append(
                {
                    "url": Template(_templates.get("task", "")).render(_context),
                    "label": task.name,
                    "type": "task",
                }
            )

        return _links

    @property
    def application(self):
        return self.environment.application

    @property
    def joined_command(self):
        if self.command:
            return " ".join(self.command)

    # ------------------------------
    # Instance methods
    # ------------------------------
    def __repr__(self):
        return f"<{self.__class__.__name__} {self.name} (type: {self.settings.type})>"

    __str__ = __repr__

    def filtered_environment_items(self, **kwargs):
        kwargs["service_name"] = self.name
        return self.config.filtered_environment_items(**kwargs)

    def image_registry_url(self, run=False, region=None):
        if self.image:
            _split = self.image.split(":")
            if len(_split) == 2:
                image = _split[0]
            else:
                image = _split[0]
            return image

        _run_string = "-run" if run else ""
        region = region or self.config.environment.collection.region

        if self.environment.application.provider_is_gcp:
            return f"{self.config.environment.collection.region}-docker.pkg.dev/{self.environment.collection.account_id}/{self.config.environment.collection.instance_name}/{self.gcr_image_name}{_run_string}"
        elif self.environment.application.provider_is_aws:
            return f"{self.environment.collection.account_id}.dkr.ecr.{region}.amazonaws.com/{self.instance_name}"

    def image_tag(self, environment_tag):
        environment_tag = environment_tag or "latest"
        if self.settings.build_config.existing_image_tag_mode == "sha":
            return environment_tag

        image_tag = environment_tag
        if self.image:
            _split = self.image.split(":")
            if len(_split) == 2:
                image_tag = _split[1]

        return image_tag

    def image_for_tag(self, environment_tag="latest", region=None, run=False):
        if self.settings.is_resource:
            return self.image or ""
        return f"{self.image_registry_url(run=run, region=region)}:{self.image_tag(environment_tag=environment_tag)}"

    def log_stream_prefix(self, task_name="web"):
        return f"{self.instance_name}-{task_name}"

    def toolbox_manager(self, environment_tag="latest"):
        return ToolboxManager(self, service_tags={self.name: environment_tag})

    def cli_info(self):
        _data = {
            "name": self.name,
            "type": self.settings.type,
        }

        if self.is_frontend or self.is_backend:
            _data["url_path"] = self.settings.url_path

        return _data
