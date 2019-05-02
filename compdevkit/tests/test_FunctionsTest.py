from compdevkit import FunctionsTest

import paramtools

class MetaParams(paramtools.Parameters):
    array_first = True
    defaults = {
        "hello_world": {
            "title": "hello world",
            "description": "test param",
            "type": "str",
            "value": "hello, world!",
            "validators": {
                "choice": {"choices": ["hello, world!", "hello, there!"]}
            }
        }
    }

class ModelParameters(paramtools.Parameters):
    defaults = {
        "schema": {
            "additional_members": {
                "checkbox": {"type": "bool"}
            }
        },
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
        }
    }

def get_inputs(meta_param_dict):
    return MetaParams().specification(meta_data=True), {"mock": ModelParameters().specification(meta_data=True)}

def validate_inputs(meta_param_dict, adjustment, errors_warnings):
    mp = ModelParameters()
    mp.adjust(adjustment["mock"], raise_errors=False)
    errors_warnings["mock"]["errors"].update(mp.errors)
    return errors_warnings

def run_model(meta_param_dict, adjustment):
    return {"renderable": [], "downloadable": []}


def test_FunctionsTest():
    ft = FunctionsTest(
        model_parameters=get_inputs,
        validate_inputs=validate_inputs,
        run_model=run_model,
        ok_adjustment={"mock": {"model_param": 2}},
        bad_adjustment={"mock": {"model_param": "not an int"}}
    )
    ft.test()