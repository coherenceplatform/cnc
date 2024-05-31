from typing import ClassVar


class EnvironmentVariableTypes:
    VARIABLE_TYPE_SECRET: ClassVar[str] = "secret"
    VARIABLE_TYPE_OUTPUT: ClassVar[str] = "output"
    VARIABLE_TYPE_STANDARD: ClassVar[str] = "standard"
    VARIABLE_TYPE_ALIAS: ClassVar[str] = "alias"

    @classmethod
    def allowed_types(cls):
        return [
            cls.VARIABLE_TYPE_STANDARD,
            cls.VARIABLE_TYPE_SECRET,
            cls.VARIABLE_TYPE_OUTPUT,
            cls.VARIABLE_TYPE_ALIAS,
        ]


class EnvironmentVariableDestinations:
    VARIABLE_TYPE_NAME: ClassVar[str] = "name"
    VARIABLE_TYPE_FILE: ClassVar[str] = "file"

    @classmethod
    def allowed_types(cls):
        return [cls.VARIABLE_TYPE_NAME, cls.VARIABLE_TYPE_FILE]
