from typing import Callable, Union
from collections import defaultdict
from datetime import datetime, date
import copy
import functools
import itertools
import random
import json

from marshmallow import fields, Schema, validate
import paramtools
import numpy as np


__version__ = "1.2.0"

Num = Union[int, float]
JSONLike = Union[dict, str]

class Parameters(paramtools.Parameters):
    def param_grid(self, param: str, step: Num =1):
        spec = self.specification(meta_data=True)
        param_spec = spec[param]
        if len(param_spec["validators"]) != 1:
            nvalidators = len(param_spec["validators"])
            raise ValueError(f"Parmeter grid can only be created with one validator. {nvalidators} are present.")
        validator_name = list(param_spec["validators"].keys())[0]
        method = self._validator_schema.WRAPPER_MAP[validator_name]
        validator = getattr(self._validator_schema, method)(
            validator_name,
            spec[param]["validators"][validator_name],
            param,
            "",
            {"value": param_spec["value"][0]["value"]},
            self.specification(use_state=False)
        )

        return validator.grid()


class Param(paramtools.BaseParamSchema):
    value = fields.List(fields.Dict)
    checkbox = fields.Bool(required=False)
    section_1 = fields.Str(required=False)
    section_2 = fields.Str(required=False)


class Params(Schema):
    parameters = fields.Dict(keys=fields.Str(), values=fields.Nested(Param), many=True)


class ErrorsWarnings(Schema):
    errors = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))
    warnings = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))


class Output(Schema):
    title = fields.Str()
    media_type = fields.Str(
        validate=validate.OneOf(choices=["bokeh", "table", "CSV", "PNG",
                                         "JPEG", "MP3", "MP4", "HDF5"])
    )
    # Data could be a string or dict. It depends on the media type.
    data = fields.Field()


class Result(Schema):
    """Serializer for load_to_S3like"""

    renderable = fields.Nested(Output, many=True)
    downloadable = fields.Nested(Output, many=True)


def serialize(data):
    def ser(obj):
        if isinstance(obj, (datetime, date)):
            return str(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    return json.loads(json.dumps(data, default=ser))

class FunctionsTest:

    def __init__(self, model_parameters: Callable, validate_inputs: Callable,
                 run_model: Callable, ok_adjustment: dict, bad_adjustment: dict):
        self.model_parameters = model_parameters
        self.validate_inputs = validate_inputs
        self.run_model = run_model
        self.ok_adjustment = ok_adjustment
        self.bad_adjustment = bad_adjustment

    def test(self):
        self.test_model_parameters()
        self.test_validate_inputs()
        self.test_run_model()

    def test_model_parameters(self):
        init_metaparams, init_modparams = self.model_parameters({})

        class MetaParams(Parameters):
            array_first = True
            defaults = init_metaparams

        metaparams = MetaParams()
        assert metaparams

        params = Params()
        for modparams in init_modparams.values():
            assert params.load({"parameters": modparams})


        mp_names = list(metaparams.specification().keys())
        mp_grid = []
        for mp_name in mp_names:
            mp_grid.append(metaparams.param_grid(mp_name))

        mp_grid = itertools.product(*mp_grid)

        for tup in mp_grid:
            _, modparams_ = self.model_parameters(
                {mp_names[i]: tup[i] for i in range(len(mp_names))}
            )
            for modparams in modparams_.values():
                assert params.load({"parameters": modparams})

    def test_validate_inputs(self):
        init_metaparams, init_modparams = self.model_parameters({})

        class MetaParams(Parameters):
            array_first = True
            defaults = init_metaparams

        mp_spec = MetaParams().specification()

        ew_template = {
            major_sect: {"errors": {}, "warnings": {}}
            for major_sect in init_modparams
        }
        ew_schema = ErrorsWarnings()

        ew_result = self.validate_inputs(mp_spec, self.ok_adjustment, copy.deepcopy(ew_template))

        for major_sect, ew_dict in ew_result.items():
            assert ew_schema.load(ew_dict)
            assert len(ew_dict.get("errors")) == 0
            assert len(ew_dict.get("warnings")) == 0

        ew_result = self.validate_inputs(mp_spec, self.bad_adjustment, copy.deepcopy(ew_template))

        for major_sect, ew_dict in ew_result.items():
            assert ew_schema.load(ew_dict)
            assert len(ew_dict.get("errors")) > 0


    def test_run_model(self):
        init_metaparams, init_modparams = self.model_parameters({})

        class MetaParams(Parameters):
            array_first = True
            defaults = init_metaparams

        mp_spec = MetaParams().specification()

        result = self.run_model(mp_spec, self.ok_adjustment)

        assert Result().load(result)
