import re
from typing import (
    Optional,
    Literal,
    ClassVar,
    List,
)
from pydantic import model_validator
from cnc.models import BaseModel
from cnc.models.custom_header import CustomHeaders, CustomHeader

from cnc.logger import get_logger

log = get_logger(__name__)


class HeaderTypeConfig(BaseModel):
    headers: List[CustomHeader]

    @model_validator(mode="before")
    def filter_headers(cls, data):
        _headers = []
        for header in data.get("headers", []):
            if header["name"] in cls.HEADER_NAMES:
                _headers.append(header)
                cls.update_data_for_header(data, header)

        data["headers"] = _headers

        return data

    @classmethod
    def update_data_for_header(cls, data, header):
        return data


class CorsConfig(HeaderTypeConfig):
    allow_credentials: Optional[bool] = False
    allow_headers: Optional[List[str]] = []
    allow_methods: Optional[List[str]] = []
    allow_origins: Optional[List[str]] = []
    expose_headers: Optional[List[str]] = []
    max_age: Optional[int] = None

    # ------------------------------
    # Properties
    # ------------------------------
    @classmethod
    def update_data_for_header(cls, data, header):
        header_name = header["name"]
        if header_name == "access-control-allow-credentials":
            data["allow_credentials"] = True
        elif header_name == "access-control-allow-headers":
            data["allow_headers"] = re.split(
                AWSCustomHeaders.HEADER_LISTVALUES_REGEX,
                header["value"],
            )
        elif header_name == "access-control-allow-methods":
            data["allow_methods"] = re.split(
                AWSCustomHeaders.HEADER_LISTVALUES_REGEX,
                header["value"],
            )
        elif header_name == "access-control-allow-origin":
            if data["allow_origins"] is None:
                data["allow_origins"] = []
            data["allow_origins"] += re.split(
                AWSCustomHeaders.HEADER_LISTVALUES_REGEX,
                header["value"],
            )
        elif header_name == "access-control-expose-headers":
            data["expose_headers"] = re.split(
                AWSCustomHeaders.HEADER_LISTVALUES_REGEX,
                header["value"],
            )
        elif header_name == "access-control-max-age":
            data["max_age"] = int(header["value"])

        return data

    HEADER_NAMES: ClassVar[List[str]] = [
        "access-control-allow-credentials",
        "access-control-allow-headers",
        "access-control-allow-methods",
        "access-control-allow-origin",
        "access-control-expose-headers",
        "access-control-max-age",
    ]


class StrictTransportConfig(BaseModel):
    max_age: Optional[int] = None
    include_subdomains: Optional[bool] = None
    preload: Optional[bool] = None


class XssConfig(BaseModel):
    mode_block: Optional[bool] = None
    enabled: Optional[bool] = None
    report_uri: Optional[str] = None


class SecurityConfig(HeaderTypeConfig):
    content_security_policy: Optional[str] = None
    frame_option: Optional[str] = None
    referrer_policy: Optional[str] = None
    content_type_options: Optional[bool] = None
    strict_transport_security: Optional[StrictTransportConfig] = None
    xss_protection: Optional[XssConfig] = None

    # ------------------------------
    # Properties
    # ------------------------------
    @classmethod
    def update_data_for_header(cls, data, header):
        header_name = header["name"]
        if header_name == "content-security-policy":
            data["content_security_policy"] = header["value"]
        elif header_name == "x-content-type-options":
            data["content_type_options"] = True
        elif header_name == "x-frame-options":
            data["frame_option"] = header["value"]
        elif header_name == "referrer-policy":
            data["referrer_policy"] = header["value"]
        elif header_name == "strict-transport-security":
            data["strict_transport_directives"] = re.split(
                AWSCustomHeaders.HEADER_DIRECTIVES_REGEX,
                header["value"],
            )
            max_age = None
            include_subdomains = None
            preload = None
            for directive in data["strict_transport_directives"]:
                if directive == "includeSubDomains":
                    include_subdomains = True
                elif directive == "preload":
                    preload = True
                elif "max-age" in directive:
                    max_age = int(directive.split("=")[1])

            data["strict_transport_security"] = {
                "max_age": max_age,
                "include_subdomains": include_subdomains,
                "preload": preload,
            }
        elif header_name == "x-xss-protection":
            xss_directives = re.split(
                AWSCustomHeaders.HEADER_DIRECTIVES_REGEX,
                header["value"],
            )

            mode_block = None
            enabled = False
            report_uri = None
            for directive in xss_directives:
                if directive == "0":
                    enabled = False
                elif directive == "1":
                    enabled = True
                elif directive == "mode=block":
                    mode_block = True
                elif "report=" in directive:
                    report_uri = directive.split("=")[1]

            data["xss_protection"] = {
                "mode_block": mode_block,
                "enabled": enabled,
                "report_uri": report_uri,
            }

        return data

    # ------------------------------
    # Class Vars
    # ------------------------------
    HEADER_NAMES: ClassVar[List[str]] = [
        "content-security-policy",
        "x-content-type-options",
        "x-frame-options",
        "referrer-policy",
        "strict-transport-security",
        "x-xss-protection",
    ]


class AWSCustomHeaders(CustomHeaders):
    provider: Literal["aws"]

    cors_config: CorsConfig
    security_config: SecurityConfig
    custom_headers: List[CustomHeader]

    # ------------------------------
    # Validators
    # ------------------------------
    @model_validator(mode="before")
    def parse_headers_config(cls, data):
        data["cors_config"] = {"headers": data["headers"]}
        data["security_config"] = {"headers": data["headers"]}

        _custom_headers = []
        exclude_from_custom_headers = (
            SecurityConfig.HEADER_NAMES
            + CorsConfig.HEADER_NAMES
            + [cls.SERVER_TIMING_HEADER]
        )
        for header in data["headers"]:
            if header["name"] not in exclude_from_custom_headers:
                _custom_headers.append(header)

        data["custom_headers"] = _custom_headers

        return data

    # ------------------------------
    # Class vars
    # ------------------------------
    SERVER_TIMING_HEADER: ClassVar[str] = "server-timing"
    HEADER_LISTVALUES_REGEX: ClassVar[str] = ",\\s*"
    HEADER_DIRECTIVES_REGEX: ClassVar[str] = ";\\s*"
