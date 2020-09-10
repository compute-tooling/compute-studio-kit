import io
import json
import fsspec

import pandas as pd
import paramtools

import cs_kit


def test_get_inputs():
    with fsspec.open(
        "cs://PSLmodels:Tax-Brain@47517/inputs/adjustment/policy", "r"
    ) as f:
        assert json.loads(f.read())

    with fsspec.open("cs://PSLmodels:Tax-Brain@47517/inputs/adjustment", "r") as f:
        assert json.loads(f.read())

    with fsspec.open(
        "cs://PSLmodels:Tax-Brain@47517/inputs/adjustment/policy", "r"
    ) as f:
        assert json.loads(f.read())

    with fsspec.open("cs://PSLmodels:Tax-Brain@47517/inputs/meta_parameters", "r") as f:
        assert json.loads(f.read())


def test_get_outputs():
    data = paramtools.read_json("cs://PSLmodels:Tax-Brain@47517/outputs")
    for output in data:
        assert isinstance(pd.read_csv(io.StringIO(output["data"])), pd.DataFrame)


def test_get_owner():
    data = paramtools.read_json("cs://PSLmodels:Tax-Brain@47517/owner")
    assert data == {"owner": "hdoupe"}


def test_get_title():
    data = paramtools.read_json("cs://PSLmodels:Tax-Brain@47517/title")
    assert data == {"title": "Test TB after updates"}
