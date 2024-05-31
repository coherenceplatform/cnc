from typing import Optional, Union
from pydantic import Field

from cnc.models.base_model import BaseModel
from cnc.logger import get_logger

log = get_logger(__name__)


class DeployResourceLimits(BaseModel):
    raw_memory: Optional[str] = Field(default="512Mi", alias="memory")
    raw_cpu: Optional[Union[int, float]] = Field(default=1, alias="cpus")
