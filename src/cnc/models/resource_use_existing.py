from typing import Optional, List

from .base_model import BaseModel, IgnoredType


# TODO: Should we use a discriminator here so we
# can have better validations etc?
class ResourceUseExistingSettings(BaseModel):
    name: str
    instance_name: str
    secret_id: Optional[str] = None
    manage_databases: Optional[bool] = True
    username: Optional[str] = None
    db_name: Optional[str] = None
    cluster_mode: Optional[bool] = False
    public_subnet_cidrs: Optional[List[str]] = None
    private_subnet_cidrs: Optional[List[str]] = None
    public_subnet_ids: Optional[List[str]] = None
    private_subnet_ids: Optional[List[str]] = None

    # ------------------------------
    # Parent relationships
    # ------------------------------

    settings: Optional[IgnoredType] = IgnoredType()
