import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="compdevkit",
    version=os.environ.get("VERSION", "0.0.0"),
    author="Hank Doupe",
    author_email="henrymdoupe@gmail.com",
    description=(
        "Developer tools for compmodels.org."
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/comp-org/Comp-Developer-Kit",
    packages=setuptools.find_packages(),
    install_requires=["paramtools>=0.5.1"],
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
)
