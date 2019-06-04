import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="compdevkit",
    version=os.environ.get("VERSION", "0.0.0"),
    author="Hank Doupe",
    author_email="henrymdoupe@gmail.com",
    description=("Developer tools for compmodels.org."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/comp-org/COMP-Developer-Toolkit",
    packages=setuptools.find_packages(),
    install_requires=["paramtools>=0.5.4", "boto3", "s3like>=1.3.1", "requests"],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "cdk-init=compdevkit.cli:init",
            "cdk-token=compdevkit.cli:comp_token",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
