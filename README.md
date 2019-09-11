# Compute Studio Kit

`cs-kit` tests your model's functions against the [Compute Studio criteria](https://docs.compute.studio/publish/functions/). If your functions pass the `cs-kit` tests, then you can be reasonably sure that the functions will work on compute.studio.

Compute Studio Kit also provides a helper command for retrieving your [Compute Studio API](https://docs.compute.studio/api/guide/) token.

## Install `cs-kit`

```bash
pip install cs-kit
```

## Set up the `csconfig` directory

```bash
csk-init
```

## Test your functions in `cs-config/cs_config/functions.py`

```python
from cs_kit import FunctionsTest

import matchups

def test_get_parameters():
    ta = FunctionsTest(
        get_inputs=matchups.get_inputs,
        validate_inputs=matchups.validate_inputs,
        run_model=matchups.get_matchup,
        ok_adjustment={"matchup": {"pitcher": [{"value": "Max Scherzer"}]}},
        bad_adjustment={"matchup": {"pitcher": [{"value": "Not a pitcher"}]}}
    )
    ta.test()

```

## Run your cs-config tests

```bash
py.test cs_config
```

## Get your [Compute Studio API](https://docs.compute.studio/api/guide/) token

```bash
$ csk-token --username myuser --password mypass
Token: your-token-here
```

## Run the compute-studio-kit tests

```bash
py.test cs_kit -v
```
