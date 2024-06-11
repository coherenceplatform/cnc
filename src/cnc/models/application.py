import yaml
import os
from pathlib import Path
from typing import Union, List, ClassVar, Optional
from pydantic import (
    Field,
    model_validator,
    field_validator,
)

from .base_model import BaseModel
from .providers.amazon.environment_collection import AWSEnvironmentCollection
from .providers.google.environment_collection import GCPEnvironmentCollection
from cnc.utils import clean_name_string

from cnc.logger import get_logger

log = get_logger(__name__)


class TemplateConfig(BaseModel):
    template_directory: Optional[str] = None
    provision_filename: Optional[str] = "main.tf.j2"
    deploy_filename: Optional[str] = "main.sh.j2"
    build_filename: Optional[str] = "main.sh.j2"

    @property
    def enabled(self):
        return bool(self.template_directory)


class Application(BaseModel):
    name: str
    provider: str
    region: Optional[str] = None
    flavor: str
    version: Union[int, float]
    collections: List[Union[AWSEnvironmentCollection, GCPEnvironmentCollection]] = (
        Field(discriminator="provider")
    )
    template_config: Optional[TemplateConfig] = Field(default_factory=TemplateConfig)

    GCP_APP_PROVIDER: ClassVar[str] = "gcp"
    AWS_APP_PROVIDER: ClassVar[str] = "aws"

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="before")
    def ensure_collection_provider(cls, data):
        for collection in data.get("collections", []):
            collection["provider"] = data.get("provider")

        return data

    @model_validator(mode="after")
    def annotate_children(self):
        for collection in self.collections:
            collection.application = self

            for environment in collection.environments:
                environment.application = self

        return self

    @field_validator("name", mode="before")
    def validate_name(cls, value: str) -> str:
        return clean_name_string(value)

    # ------------------------------
    # Class methods
    # ------------------------------
    @classmethod
    def from_environments_yml(
        cls, data_file_path: Path, config_file_path: Path = "cnc.yml"
    ):
        with open(data_file_path) as parsed_data:
            env_yml_data = yaml.safe_load(parsed_data)
        return cls.model_validate(
            env_yml_data,
            context={
                "config_file_path": str(config_file_path),
                "provider": env_yml_data.get("provider"),
            },
        )

    @classmethod
    def from_environments_data(cls, data):
        return cls.model_validate(
            data,
            context={"provider": data.get("provider")},
        )

    # ------------------------------
    # Properties
    # ------------------------------
    @property
    def default_collection(self):
        for collection in self.collections:
            if collection.default:
                return collection

        log.debug(
            f"no default provided - returning first collection as default for {self}"
        )
        # only happens if no default defined
        return self.collections[0]

    @property
    def provider_is_gcp(self):
        return self.provider == self.GCP_APP_PROVIDER

    @property
    def provider_is_aws(self):
        return self.provider == self.AWS_APP_PROVIDER

    @property
    def config_files_path(self):
        return (
            f"{self.config_files_parent_dir}/app_{self.name}/"
            f"{self.provider}_{self.flavor}/{self.version}"
        )

    @property
    def config_files_parent_dir(self):
        return f"/tmp/.cnc_tmp_{self.name}"

    @property
    def environments(self):
        if not hasattr(self, "_envs"):
            self._envs = []

        if not self._envs:
            for collection in self.collections:
                for e in collection.environments:
                    self._envs.append(e)

        return self._envs

    @property
    def flavor_metadata(self):
        # load the .metadata file from the top level of the flavor directory
        with open(self.metadata_file) as metadata_file:
            return yaml.safe_load(metadata_file.read())

    @property
    def metadata_file(self):
        src_dir = Path(__file__).parent.parent

        # TODO: check for a metadata file in the custom template directory, if configured

        # copy flavor-specific metadata file
        flavor_metadata = (
            f"{src_dir}/flavors/{self.provider}"
            f"/{self.flavor}/{self.version}/.metadata"
        )
        if os.path.isfile(flavor_metadata):
            return flavor_metadata

        # copy included shared metadata file
        included_metadata = f"{src_dir}/flavors/{self.provider}" f"/shared/.metadata"
        if os.path.isfile(included_metadata):
            return included_metadata

    # ------------------------------
    # Instance methods
    # ------------------------------
    def __repr__(self):
        return (
            f"<Application (name: {self.name} | provider: {self.provider} "
            f"({self.flavor}/{self.version}))>"
        )

    __str__ = __repr__

    def collection_by_name(self, collection_name=None):
        if collection_name:
            for collection in self.collections:
                if collection.name == collection_name:
                    return collection
        else:
            return self.default_collection
