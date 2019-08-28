from pathlib import Path
import argparse

import requests

functionstemplate = "# Write or import your Compute Studio functions here."

testfunctionstemplate = """from cskit import FunctionsTest

from cskit import functions


def test_functions():
    # test your functions with FunctionsTest here
    pass
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
    name="csconfig",
    description="Compute Studio configuration files.",
    url="https://github.com/compute-studio-org/Compute-Studio-Toolkit",
    packages=setuptools.find_packages(),
    include_package_data=True,
)
"""

installtemplate = "# bash commands for installing your package"


def write_template(path, template):
    if not path.exists():
        with open(path, "w") as f:
            f.write(template)


def init():
    cstoplevel = Path.cwd() / "csconfig"
    cstoplevel.mkdir(exist_ok=True)
    write_template(cstoplevel / "setup.py", setuptemplate)
    write_template(cstoplevel / "install.sh", installtemplate)

    cs = cstoplevel / "csconfig"
    cs.mkdir(exist_ok=True)

    (cs / "__init__.py").touch()

    write_template(cs / "functions.py", functionstemplate)

    test = cs / "tests"
    test.mkdir(exist_ok=True)

    (test / "__init__.py").touch()

    write_template(test / "test_functions.py", testfunctionstemplate)


def cs_token():
    parser = argparse.ArgumentParser(description="Helper for getting Compute Studio credentials.")
    parser.add_argument("--username", help="Compute Studio username", required=True)
    parser.add_argument("--password", help="Compute Studio password", required=True)
    parser.add_argument("--quiet", "-q", help="Just print token", required=False, action="store_true")
    args = parser.parse_args()

    resp = requests.post(
        "https://compute.studio/api-token-auth/",
        json={"username": args.username, "password": args.password}
    )
    if resp.status_code == 200:
        if args.quiet:
            print(resp.json()["token"])
        else:
            print("Token: ", resp.json()["token"])
    else:
        print("Authentication failed.")