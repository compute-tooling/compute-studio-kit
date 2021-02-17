from pathlib import Path
import argparse

import requests

from cs_kit import buildpacks

functionstemplate = """# Write or import your Compute Studio functions here.


def get_version():
    pass


def get_inputs(meta_param_dict):
    pass


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    pass


def run_model(meta_param_dict, adjustment):
    pass
"""

testfunctionstemplate = """from cs_kit import CoreTestFunctions

from cs_config import functions


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment = {}  # your valid inputs here
    bad_adjustment = {}  # your invalid inputs here

"""

setuptemplate = """\"\"\"
setup.py is used to build a light-weight python package around your
Compute Studio code. Add a MANIFEST.in file to specify data files that should
be included with this package. Read more here:
https://docs.python.org/3.8/distutils/sourcedist.html#specifying-the-files-to-distribute
\"\"\"

import setuptools
import os

setuptools.setup(
    name="cs-config",
    description="Compute Studio configuration files.",
    url="https://github.com/compute-tooling/compute-studio-kit",
    packages=setuptools.find_packages(),
    include_package_data=True,
)
"""

installtemplate = "# bash commands for installing your package"


def write_template(path, template):
    if not path.exists():
        with open(path, "w") as f:
            f.write(template)


def init(args: argparse.Namespace = None):
    cstoplevel = Path.cwd() / "cs-config"
    cstoplevel.mkdir(exist_ok=True)
    write_template(cstoplevel / "install.sh", installtemplate)

    if args.app_type == "model":
        write_template(cstoplevel / "setup.py", setuptemplate)
        cs = cstoplevel / "cs_config"
        cs.mkdir(exist_ok=True)

        (cs / "__init__.py").touch()

        test = cs / "tests"
        test.mkdir(exist_ok=True)

        (test / "__init__.py").touch()

        write_template(cs / "functions.py", functionstemplate)

        write_template(test / "test_functions.py", testfunctionstemplate)


def get_token(host, username, password, quiet=False):
    resp = requests.post(
        f"{host}/api-token-auth/", json={"username": username, "password": password},
    )
    if resp.status_code == 200:
        if quiet:
            print(resp.json()["token"])
        else:
            print("Token: ", resp.json()["token"])
    else:
        print("Authentication failed.")


def cs_token(subparsers: argparse._SubParsersAction = None):
    description = "Helper for getting Compute Studio credentials."
    if subparsers is None:
        # support for legacy csk-token command.
        parser = argparse.ArgumentParser(description=description)
    else:
        parser = subparsers.add_parser("token", description=description)
    parser.add_argument("--username", help="Compute Studio username", required=True)
    parser.add_argument("--password", help="Compute Studio password", required=True)
    parser.add_argument(
        "--quiet", "-q", help="Just print token", required=False, action="store_true"
    )
    parser.add_argument(
        "--host",
        help="Use another Compute Studio host besides https://compute.studio",
        default="https://compute.studio",
    )
    if subparsers is None:
        args = parser.parse_args()
        get_token(args.host, args.username, args.password, args.quiet)
    else:
        parser.set_defaults(
            func=lambda args: get_token(
                args.host, args.username, args.password, args.quiet
            )
        )


def build_env(subparsers: argparse._SubParsersAction):
    parser = subparsers.add_parser(
        "build-env",
        description="Build packages for Compute Studio app using available configuration files.",
    )
    parser.set_defaults(func=lambda args: buildpacks.build_env())


def cli():
    parser = argparse.ArgumentParser(description="C/S CLI")
    subparsers = parser.add_subparsers()

    cs_token(subparsers)
    build_env(subparsers)

    init_parser = subparsers.add_parser(
        "init", description="Initialize cs-config package."
    )
    init_parser.add_argument("--app-type", default="model", required=False)
    init_parser.set_defaults(func=init)

    args = parser.parse_args()
    args.func(args)
