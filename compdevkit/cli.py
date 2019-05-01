from pathlib import Path

def init():
    comp = Path.cwd() / "comp"
    comp.mkdir()
    compinit = comp / "__init__.py"
    compinit.touch()
    compfunctions = comp / "functions.py"
    compfunctions.touch()

    test = comp / "tests"
    test.mkdir()
    testinit = test / "__init__.py"
    testinit.touch()
    testfunctions  = test / "test_functions.py"
    testfunctions.touch()
