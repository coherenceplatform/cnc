from pydantic import (
    BaseModel as PydanticBaseModel,
    model_validator,
    ValidationInfo,
)

from cnc.logger import get_logger

log = get_logger(__name__)


class IgnoredType:
    pass


class BaseModel(PydanticBaseModel):
    @model_validator(mode="before")
    @classmethod
    def ensure_provider(cls, data: dict, info: ValidationInfo):
        if info.context:
            data["provider"] = info.context.get("provider")

        return data

    @classmethod
    def convert_dict_keys_to_names(cls, value: dict) -> list[dict]:
        with_names = []

        for k, v in value.items():
            if not isinstance(v, dict):
                raise ValueError(f"{k} is not a dict, bad data format")

            v.update({"name": k})
            with_names.append(v)

        return with_names

    class Config:
        ignored_types = (IgnoredType,)
        arbitrary_types_allowed = True
