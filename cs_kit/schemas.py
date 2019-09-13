from typing import Union

from marshmallow import fields, Schema
import paramtools


num = Union[int, float]


class Parameters(paramtools.Parameters):
    def param_grid(self, param: str, step: num = 1):
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
            {"value": param_spec["value"][0]["value"]},
            self.specification(use_state=False),
        )

        return validator.grid()


class ErrorsWarnings(Schema):
    errors = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))
    warnings = fields.Dict(keys=fields.Str(), values=fields.List(fields.Str()))
