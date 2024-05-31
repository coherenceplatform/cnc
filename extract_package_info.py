import toml

with open("pyproject.toml", "r") as f:
    pyproject = toml.load(f)

package_name = pyproject["tool"]["poetry"]["name"]
package_version = pyproject["tool"]["poetry"]["version"]

with open("env_output.txt", "w") as env_f:
    env_f.write(f"PACKAGE_NAME={package_name}\n")
    env_f.write(f"PACKAGE_VERSION={package_version}\n")
