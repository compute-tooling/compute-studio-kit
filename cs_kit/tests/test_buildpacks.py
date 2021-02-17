from pathlib import Path
import pytest

from cs_kit import buildpacks


current_dir = Path(__file__).resolve().parent


def test_buildpacks(monkeypatch):
    cmds = []
    monkeypatch.setattr(buildpacks, "run", lambda cmd: cmds.append(cmd))

    buildpacks.PythonBuildpack().build()
    assert cmds == [
        "conda install -y paramtools pytest requests pip pandas pre-commit black flake8 fsspec",
        "pip install cs-storage",
    ]

    cmds[:] = []
    buildpacks.PythonBuildpack(
        environment_yml_path=Path(current_dir / "mock_environment.yml")
    ).build()
    assert cmds == [
        "conda install -y paramtools pytest requests pip pandas pre-commit black flake8 fsspec",
        "pip install cs-storage",
        "pip install -e .",
    ]

    cmds[:] = []
    buildpacks.PythonBuildpack(
        environment_yml_path="dne.yml",
        requirements_txt_path=Path(current_dir / "mock_requirements.txt"),
    ).build()
    assert cmds == [
        "pip install cs-kit",
    ]
