from typing import Callable, Union
from collections import defaultdict
from datetime import datetime, date
import copy
import functools
import itertools
import random
import json

from marshmallow import fields, Schema
import paramtools
import numpy as np

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
    section_1 = fields.Str()
    section_2 = fields.Str()

class Params(Schema):
    parameters = fields.Dict(keys=fields.Str(), values=fields.Nested(Param), many=True)


class ErrorsWarnings(Schema):
    errors = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))
    warnings = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))

def serialize(data):
    def ser(obj):
        if isinstance(obj, (datetime, date)):
            return str(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return obj
    return json.loads(json.dumps(data, default=ser))

class TestAPI:

    def __init__(self, model_parameters: Callable, validate_inputs: Callable,
                 run_model: Callable, schema: JSONLike =None):
        self.model_parameters = model_parameters
        self.validate_inputs = validate_inputs
        self.run_model = run_model
        self.schema = schema
    
    def test(self):
        self.test_model_parameters()
        self.test_validate_inputs()
    
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

        schema = {
            "schema": {
                "additional_members": {
                    "section_1": {"type": "str"},
                    "section_2": {"type": "str"}
                }
            }
        }
        
        modparams_dict = {}
        for major_sect, params in init_modparams.items():
            defaults_ = serialize({
                k: dict(v, **{"value": v["value"][0]["value"]})
                for k, v in params.items()
            })
            defaults_.update(schema)
            class ModParams(Parameters):
                defaults = defaults_
            modparams_dict[major_sect] = ModParams()
       
        ew_template = {
            major_sect: {"errors": {}, "warnings": {}}
            for major_sect in init_modparams
        }
        ew_schema = ErrorsWarnings()
        adj = defaultdict(dict)
        for major_sect, modparams in modparams_dict.items():
            print('doing major sect', major_sect)
            for param in modparams.specification():
                print('doing param', param)
                try:
                    rand = random.choice(modparams.param_grid(param))
                except ValueError:
                    continue
                nd = modparams._data[param]["number_dims"]
                while nd > 0:
                    rand = [rand]
                    nd -= 1
                mini_adj = serialize({param: rand})
                modparams.adjust(mini_adj)
                adj[major_sect].update(mini_adj)
                ew = self.validate_inputs(
                    init_metaparams, 
                    {major_sect: mini_adj}, 
                    copy.deepcopy(ew_template)
                )
                assert ew_schema.loads(json.dumps(ew[major_sect]))

        ew = self.validate_inputs(init_metaparams, adj, copy.deepcopy(ew_template))
        for major_sect in ew:
            assert ew_schema.loads(json.dumps(serialize(ew[major_sect])))
