import time
import subprocess
import yaml
from pathlib import Path


class PythonBuildpack:
    def __init__(
        self,
        environment_yml_path="environment.yml",
        requirements_txt_path="requirements.txt",
    ):
        self.environment_yml_path = environment_yml_path
        self.requirements_txt_path = requirements_txt_path

    def get_requirements(self):
        pip_requirements = []
        conda_requirements = []
        if Path(self.environment_yml_path).exists():
            with open(self.environment_yml_path) as f:
                env = yaml.safe_load(f.read())

            dependencies = env["dependencies"]
            for dep in dependencies:
                if isinstance(dep, dict) and dep.get("pip"):
                    pip_requirements = dep["pip"]
                else:
                    if ">" in dep or "<" in dep:
                        dep = dep.replace('"', "")
                        dep = f'"{dep}"'
                    conda_requirements.append(dep)

        if Path(self.requirements_txt_path).exists():
            with open(self.requirements_txt_path, "r") as f:
                pip_requirements = f.read().split("\n")

        return {
            "pip_requirements": pip_requirements,
            "conda_requirements": conda_requirements,
        }

    def build(self):
        reqs = self.get_requirements()
        if reqs["conda_requirements"]:
            run(f"conda install -y {' '.join(reqs['conda_requirements'])}")
        if reqs["pip_requirements"]:
            pip_requirements = []
            local_install = False
            for req in reqs["pip_requirements"]:
                if req == "-e .":
                    local_install = True
                else:
                    pip_requirements.append(req)

            run(f"pip install {' '.join(pip_requirements)}")
            if local_install:
                run("pip install -e .")


buildpacks = [PythonBuildpack]


def build_env():
    for buildpack in buildpacks:
        buildpack().build()


def run(cmd):
    print(f"Running: {cmd}\n")
    s = time.time()
    res = subprocess.run(cmd, shell=True, check=True)
    f = time.time()
    print(f"\n\tFinished in {f-s} seconds.\n")
    return res
