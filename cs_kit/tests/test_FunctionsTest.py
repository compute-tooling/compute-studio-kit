import pytest
import paramtools

from cs_kit import CoreTestFunctions, CSKitError, SerializationError


class MetaParams(paramtools.Parameters):
    array_first = True
    defaults = {
        "hello_world": {
            "title": "hello world",
            "description": "test param",
            "type": "str",
            "value": "hello, world!",
            "validators": {"choice": {"choices": ["hello, world!", "hello, there!"]}},
        }
    }


class ModelParameters(paramtools.Parameters):
    defaults = {
        "schema": {"additional_members": {"checkbox": {"type": "bool"}}},
        "model_param": {
            "title": "Model Param",
            "description": "A model param",
            "type": "int",
            "value": [{"value": 1}],
        },
        "checkbox_param": {
            "title": "Checkbox Param",
            "description": "A checkbox param",
            "type": "int",
            "checkbox": True,
            "value": [{"value": 4}],
        },
    }


def get_version():
    return "1.0.0"


def get_inputs(meta_param_dict):
    return {
        "meta_parameters": MetaParams().dump(),
        "model_parameters": {"mock": ModelParameters().dump()},
    }


def get_inputs_ser_error(meta_param_dict):
    return {
        "meta_parameters": MetaParams().dump(),
        "model_parameters": {
            "mock": ModelParameters().specification(meta_data=True, serializable=False)
        },
    }


def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    mp = ModelParameters()
    mp.adjust(adjustment["mock"], raise_errors=False)
    errors_warnings["mock"]["errors"].update(mp.errors)
    return {"errors_warnings": errors_warnings}


def validate_inputs_returns_custom_adj(meta_param_dict, adjustment, errors_warnings):
    mp = ModelParameters()
    mp.adjust(adjustment["mock"], raise_errors=False)
    errors_warnings["mock"]["errors"].update(mp.errors)
    return {"errors_warnings": errors_warnings, "custom_adjustment": {"my": "params"}}


def run_model_old_bokeh(meta_param_dict, adjustment):
    return {
        "renderable": [
            {
                "media_type": "bokeh",
                "title": "bokeh plot",
                "data": {"html": "<div/>", "javascript": "console.log('hello world')"},
            },
            {"media_type": "table", "title": "table stuff", "data": "<table/>"},
        ],
        "downloadable": [
            {"media_type": "CSV", "title": "CSV file", "data": "comma,sep,values\n"},
            {"media_type": "PDF", "title": "PDF file", "data": b"pdf data"},
        ],
    }


def run_model(meta_param_dict, adjustment):
    return {
        "renderable": [
            {
                "media_type": "bokeh",
                "title": "bokeh plot",
                "data": {
                    "target_id": "abc",
                    "root_id": "123",
                    "doc": "console.log('hello world')",
                },
            },
            {"media_type": "table", "title": "table stuff", "data": "<table/>"},
        ],
        "downloadable": [
            {"media_type": "CSV", "title": "CSV file", "data": "comma,sep,values\n"},
            {"media_type": "PDF", "title": "PDF file", "data": b"pdf data"},
        ],
    }


class TestFunctions1(CoreTestFunctions):
    get_version = get_version
    get_inputs = get_inputs
    validate_inputs = validate_inputs
    run_model = run_model
    ok_adjustment = {"mock": {"model_param": 2}}
    bad_adjustment = {"mock": {"model_param": "not an int"}}


def test_serialization_error():
    class TestFunctions(CoreTestFunctions):
        get_version = get_version
        get_inputs = get_inputs_ser_error
        validate_inputs = validate_inputs
        run_model = run_model
        ok_adjustment = {"mock": {"model_param": 2}}
        bad_adjustment = {"mock": {"model_param": "not an int"}}

    ft = TestFunctions()
    with pytest.raises(SerializationError):
        ft.test_get_inputs()


def test_missing_functions():
    class TestFunctions(CoreTestFunctions):
        pass

    ft = TestFunctions()
    with pytest.raises(AttributeError):
        ft.get_inputs({})


class TestFunctions3(CoreTestFunctions):
    get_version = get_version
    get_inputs = get_inputs
    validate_inputs = validate_inputs_returns_custom_adj
    run_model = run_model
    ok_adjustment = {"mock": {"model_param": 2}}
    bad_adjustment = {"mock": {"model_param": "not an int"}}


def test_key_errors_on_get_inputs():
    class TestFunctions(CoreTestFunctions):
        get_version = get_version
        get_inputs = lambda *args: "hello world"
        validate_inputs = validate_inputs
        run_model = run_model
        ok_adjustment = {"mock": {"model_param": 2}}
        bad_adjustment = {"mock": {"model_param": "not an int"}}

    ft = TestFunctions()
    with pytest.raises(CSKitError):
        ft.test_get_inputs()

    class TestFunctions(CoreTestFunctions):
        get_version = get_version
        get_inputs = lambda *args: {"param_meta": {}, "model_parameters": {}}
        validate_inputs = validate_inputs
        run_model = run_model
        ok_adjustment = {"mock": {"model_param": 2}}
        bad_adjustment = {"mock": {"model_param": "not an int"}}

    ft = TestFunctions()
    with pytest.raises(CSKitError):
        ft.test_get_inputs()


def test_key_errors_on_validate_inputs():
    class TestFunctions(CoreTestFunctions):
        get_version = get_version
        get_inputs = get_inputs
        validate_inputs = lambda *args: "hello world"
        run_model = run_model
        ok_adjustment = {"mock": {"model_param": 2}}
        bad_adjustment = {"mock": {"model_param": "not an int"}}

    ft = TestFunctions()
    with pytest.raises(CSKitError):
        ft.test_validate_inputs()

    class TestFunctions(CoreTestFunctions):
        get_version = get_version
        get_inputs = get_inputs
        validate_inputs = lambda *args: {"heyo": {}}
        run_model = run_model
        ok_adjustment = {"mock": {"model_param": 2}}
        bad_adjustment = {"mock": {"model_param": "not an int"}}

    ft = TestFunctions()
    with pytest.raises(CSKitError):
        ft.test_validate_inputs()

    class TestFunctions(CoreTestFunctions):
        get_version = get_version
        get_inputs = get_inputs
        validate_inputs = lambda *args: {
            "errors_warnings": {},
            "custom_adjustment": {},
            "heyo": 2,
        }
        run_model = run_model
        ok_adjustment = {"mock": {"model_param": 2}}
        bad_adjustment = {"mock": {"model_param": "not an int"}}

    ft = TestFunctions()
    with pytest.raises(CSKitError):
        ft.test_validate_inputs()


def test_old_bokeh_outputs():
    class TestFunctions(TestFunctions1):
        run_model = run_model_old_bokeh

    tf = TestFunctions()
    with pytest.raises(CSKitError):
        tf.test_run_model()
