from setuptools import setup
import toml
import setuptools


def read_pyproject():
    with open("pyproject.toml", "r", encoding="utf-8") as f:
        return toml.load(f)


def build_setup_args():
    pyproject = read_pyproject()
    poetry_config = pyproject["tool"]["poetry"]

    # Map the necessary parts from the pyproject.toml to setup() arguments
    return {
        "name": poetry_config["name"],
        "version": "0.1",
        "description": poetry_config["description"],
        "author": ", ".join(a for a in poetry_config["authors"]),
        "packages": setuptools.find_packages(where="src"),
        "package_dir": {"": "src"},
        "entry_points": {"console_scripts": ["cnc=src.main:app"]},
        "install_requires": [str(v) for v in poetry_config["dependencies"].values()],
        "extras_require": {
            "dev": [
                str(v)
                for v in pyproject["tool"]["poetry"]["group"]["dev"][
                    "dependencies"
                ].values()
            ],
        },
    }


setup(**build_setup_args())
