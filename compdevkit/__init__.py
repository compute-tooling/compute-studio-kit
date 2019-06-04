from typing import Callable, Union
from collections import defaultdict
from datetime import datetime, date
import copy
import functools
import itertools
import random
import json
import uuid

from marshmallow import fields, Schema, validate
import paramtools
import numpy as np
import s3like

from .exceptions import SerializationError


__version__ = "1.5.0"

Num = Union[int, float]
JSONLike = Union[dict, str]


class Parameters(paramtools.Parameters):
    def param_grid(self, param: str, step: Num = 1):
        spec = self.specification(meta_data=True)
        param_spec = spec[param]
        if len(param_spec["validators"]) != 1:
            nvalidators = len(param_spec["validators"])
            raise ValueError(
                f"Parmeter grid can only be created with one validator. {nvalidators} are present."
            )
        validator_name = list(param_spec["validators"].keys())[0]
        method = self._validator_schema.WRAPPER_MAP[validator_name]
        validator = getattr(self._validator_schema, method)(
            validator_name,
            spec[param]["validators"][validator_name],
            param,
            "",
            {"value": param_spec["value"][0]["value"]},
            self.specification(use_state=False),
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
        validate=validate.OneOf(
            choices=["bokeh", "table", "CSV", "PNG", "JPEG", "MP3", "MP4", "HDF5"]
        )
    )
    # Data could be a string or dict. It depends on the media type.
    data = fields.Field()


class Result(Schema):
    """Serializer for load_to_S3like"""
    model_version = fields.Str()
    renderable = fields.Nested(Output, many=True)
    downloadable = fields.Nested(Output, many=True)


class FunctionsTest:
    def __init__(
        self,
        get_inputs: Callable,
        validate_inputs: Callable,
        run_model: Callable,
        ok_adjustment: dict,
        bad_adjustment: dict,
    ):
        self.get_inputs = get_inputs
        self.validate_inputs = validate_inputs
        self.run_model = run_model
        self.ok_adjustment = ok_adjustment
        self.bad_adjustment = bad_adjustment

    def test(self):
        self.test_get_inputs()
        self.test_validate_inputs()
        self.test_run_model()

    def test_get_inputs(self):
        init_metaparams, init_modparams = self.get_inputs({})

        try:
            json.dumps(init_metaparams)
        except TypeError as e:
            raise SerializationError(
                (
                    f"Meta parameters must be JSON serializable: \n\n\t{str(e)}\n"
                    f"\nHint: try setting `serializable=True` in `Parameters.specification`."
                )
            )
        try:
            json.dumps(init_modparams)
        except TypeError as e:
            raise SerializationError(
                (
                    f"Model parameters must be JSON serializable: \n\n\t{str(e)}\n"
                    f"\nHint: try setting `serializable=True` in `Parameters.specification`."
                )
            )

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
            _, modparams_ = self.get_inputs(
                {mp_names[i]: tup[i] for i in range(len(mp_names))}
            )
            for modparams in modparams_.values():
                assert params.load({"parameters": modparams})

    def test_validate_inputs(self):
        init_metaparams, init_modparams = self.get_inputs({})

        class MetaParams(Parameters):
            array_first = True
            defaults = init_metaparams

        mp_spec = MetaParams().specification()

        ew_template = {
            major_sect: {"errors": {}, "warnings": {}} for major_sect in init_modparams
        }
        ew_schema = ErrorsWarnings()

        res = self.validate_inputs(
            mp_spec, self.ok_adjustment, copy.deepcopy(ew_template)
        )
        if isinstance(res, tuple):
            ew_result, parsedparams = res
        else:
            ew_result = res
            parsedparams = ()

        for _, ew_dict in ew_result.items():
            assert ew_schema.load(ew_dict)
            assert len(ew_dict.get("errors")) == 0
            assert len(ew_dict.get("warnings")) == 0

        if parsedparams:
            try:
                json.dumps(parsedparams)
            except TypeError as e:
                raise SerializationError(
                    f"Parameters must be JSON serializable: \n\n\t{str(e)}\n"
                )

        res = self.validate_inputs(
            mp_spec, self.bad_adjustment, copy.deepcopy(ew_template)
        )
        if isinstance(res, tuple):
            ew_result, parsedparams = res
        else:
            ew_result = res
            parsedparams = ()

        for major_sect, ew_dict in ew_result.items():
            assert ew_schema.load(ew_dict)
            assert len(ew_dict.get("errors")) > 0

        if parsedparams:
            try:
                json.dumps(parsedparams)
            except TypeError as e:
                raise SerializationError(
                    f"Parameters must be JSON serializable: \n\n\t{str(e)}\n"
                )

    def test_run_model(self):
        init_metaparams, init_modparams = self.get_inputs({})

        class MetaParams(Parameters):
            array_first = True
            defaults = init_metaparams

        mp_spec = MetaParams().specification()

        result = self.run_model(mp_spec, self.ok_adjustment)

        assert Result().load(result)
        assert result.pop("model_version")
        assert s3like.write_to_s3like(uuid.uuid4(), result, do_upload=False)
