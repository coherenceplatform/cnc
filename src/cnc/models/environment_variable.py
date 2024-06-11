import hashlib
import traceback

from typing import Optional
from pydantic import model_validator, ValidationInfo, Field
from jinja2 import Template

from .base_model import BaseModel, IgnoredType

from cnc.constants import EnvironmentVariableTypes, EnvironmentVariableDestinations
from cnc.utils import clean_name_string
from cnc.logger import get_logger

log = get_logger(__name__)


class EnvironmentVariable(
    BaseModel, EnvironmentVariableTypes, EnvironmentVariableDestinations
):
    name: Optional[str] = None

    service: Optional[str] = None
    raw_value: Optional[str] = Field(default=None, alias="value")
    raw_secret_id: Optional[str] = Field(default=None, alias="secret_id")
    raw_output_name: Optional[str] = Field(default=None, alias="output_name")
    alias: Optional[str] = None

    collection: Optional[IgnoredType] = Field(default_factory=IgnoredType)
    environment: Optional[IgnoredType] = Field(default_factory=IgnoredType)

    @model_validator(mode="before")
    def validate_existing_info(cls, data: dict, info: ValidationInfo):
        if not (
            data.get("value")
            or data.get("secret_id")
            or data.get("output_name")
            or data.get("alias")
        ):
            raise ValueError(
                "value or secret_id or output_name or alias must be specified"
            )
        return data

    @property
    def instance_name(self):
        base_name = self.collection.instance_name
        if self.environment:
            base_name = self.environment.instance_name

        _hash = hashlib.sha256()
        _hash.update(base_name.encode())
        _hash.update(self.name.encode())
        namespace = f"{_hash.hexdigest()[:11]}"

        return clean_name_string(f"e{namespace}-{self.name}")

    @property
    def secret_id(self):
        if self.variable_type == self.VARIABLE_TYPE_ALIAS:
            for other_variable in self.environment.environment_variables:
                if other_variable.name == self.alias:
                    return other_variable.secret_id
        if self.variable_type == self.VARIABLE_TYPE_SECRET:
            return self.raw_secret_id

    @property
    def output_name(self):
        if self.variable_type == self.VARIABLE_TYPE_ALIAS:
            for other_variable in self.environment.environment_variables:
                if other_variable.name == self.alias:
                    return other_variable.output_name
        if self.variable_type == self.VARIABLE_TYPE_OUTPUT:
            template = Template(self.raw_output_name)
            context = {
                "environment": {"name": self.environment.name},
                "collection": {
                    "name": self.collection.name or self.environment.collection.name
                },
            }
            return template.render(context)

    @property
    def value(self):
        try:
            if self.variable_type == self.VARIABLE_TYPE_SECRET:
                return self.environment.collection.get_secret_value(self.secret_id)
            if self.variable_type == self.VARIABLE_TYPE_STANDARD:
                return self.raw_value
            if self.variable_type == self.VARIABLE_TYPE_OUTPUT:
                return self.environment.collection.get_terraform_output(
                    self.output_name
                )
            if self.variable_type == self.VARIABLE_TYPE_ALIAS:
                for other_variable in self.environment.environment_variables:
                    if other_variable.name == self.alias:
                        return other_variable.value
        except Exception:
            log.warning(
                f"Cannot get value for variable {self.name}: {traceback.format_exc()}"
            )
            return ""

    @property
    def variable_type(self):
        if self.alias:
            return self.VARIABLE_TYPE_ALIAS
        elif self.raw_secret_id:
            return self.VARIABLE_TYPE_SECRET
        elif self.raw_output_name:
            return self.VARIABLE_TYPE_OUTPUT
        elif self.raw_value:
            return self.VARIABLE_TYPE_STANDARD
        else:
            log.warning(f"Unknown secret type: {self}")
