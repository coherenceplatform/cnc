from typing import Optional

from .base_model import BaseModel


class Stage(BaseModel):
    name: str
    provider_token: Optional[str] = ""
    callback_url: Optional[str] = ""

    def __getattribute__(self, item):
        # Override to catch "is_<name>" pattern
        if item.startswith("is_"):
            name_to_check = item[3:]

            if name_to_check not in ["build", "deploy"]:
                # preserve default attributes of BaseModel if not a valid cnc stage name
                return super().__getattribute__(item)

            # Compare with the instance's name property
            if name_to_check == super().__getattribute__("name"):
                return True
            return False
        else:
            return super().__getattribute__(item)
