# Comp-Developer-Toolkit

`compdevkit` tests your model's endpoints against the COMP criteria. If your endpoints pass the `compdevkit` tests, then you can be reasonably sure that the endpoints will work on COMPmodels.org.

## Example

```python
from compdevkit import TestEndpoints

import matchups

def test_get_parameters():
    ta = TestEndpoints(
        model_parameters=matchups.get_inputs,
        validate_inputs=matchups.validate_inputs,
        run_model=matchups.get_matchup,
        ok_adjustment={"matchup": {"pitcher": [{"value": "Max Scherzer"}]}},
        bad_adjustment={"matchup": {"pitcher": [{"value": "Not a pitcher"}]}}
    )
    ta.test()

```

## Installation

```bash
pip install git+https://github.com/comp-org/Developer-Tools.git@master
```