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
from cs_kit import CoreTestFunctions

from cs_config import functions


class TestFunctions1(CoreTestFunctions):
    get_version = functions.get_version
    get_inputs = functions.get_inputs
    validate_inputs = functions.validate_inputs
    run_model = functions.run_model
    ok_adjustment={"matchup": {"pitcher": [{"value": "Max Scherzer"}]}}
    bad_adjustment={"matchup": {"pitcher": [{"value": "Not a pitcher"}]}}

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
