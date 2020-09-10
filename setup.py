import setuptools
import os

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="cs-kit",
    version=os.environ.get("VERSION", "0.0.0"),
    author="Hank Doupe",
    author_email="henrymdoupe@gmail.com",
    description=("Developer tools for compute.studio."),
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/compute-studio-org/Compute-Studio-Toolkit",
    packages=setuptools.find_packages(),
    install_requires=["paramtools", "cs-storage", "pandas", "fsspec"],
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "csk-init=cs_kit.cli:init",
            "csk-token=cs_kit.cli:cs_token",
            "csk=cs_kit.cli:cli",
        ]
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
