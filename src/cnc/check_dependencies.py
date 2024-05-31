import shutil
import sys

from .logger import get_logger

log = get_logger(__name__)


def check_deps(application=None):
    # add provider-specific ones
    # check bash shell available
    # print info of what version of each is installed
    # print tested versions?

    dep_list = ["terraform", "jq"]

    if application.provider == "gcp":
        dep_list.append("gcloud")
    elif application.provider == "aws":
        dep_list.append("aws")

    for tool_name in dep_list:
        check_if_installed(tool_name)


def check_if_installed(tool_name):
    if shutil.which(tool_name) is None:
        log.warning(f"Error: The required program '{tool_name}' is not installed.")
        sys.exit(1)
