from pathlib import Path

functionstemplate = "# Write or import your COMP functions here."

testfunctionstemplate = """from compdevkit import FunctionsTest

from compconfig import functions


def test_functions():
    # test your functions with FunctionsTest here
    pass
"""

setuptemplate = """\"\"\"
setup.py is used to build a light-weight python package around your
COMP code. Add a MANIFEST.in file to specify data files that should
be included with this package. Read more here:
https://docs.python.org/3.8/distutils/sourcedist.html#specifying-the-files-to-distribute
\"\"\"

import setuptools
import os

setuptools.setup(
    name="compconfig",
    description="COMP configuration files.",
    url="https://github.com/comp-org/COMP-Developer-Toolkit",
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
    comptoplevel = Path.cwd() / "compconfig"
    comptoplevel.mkdir(exist_ok=True)
    write_template(comptoplevel / "setup.py", setuptemplate)
    write_template(comptoplevel / "install.sh", installtemplate)

    comp = comptoplevel / "compconfig"
    comp.mkdir(exist_ok=True)

    (comp / "__init__.py").touch()

    write_template(comp / "functions.py", functionstemplate)

    test = comp / "tests"
    test.mkdir(exist_ok=True)

    (test / "__init__.py").touch()

    write_template(test / "test_functions.py", testfunctionstemplate)
