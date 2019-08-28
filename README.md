# Compute Studio Kit

`cskit` tests your model's functions against the [Compute Studio criteria](https://docs.compute.studio/publish/functions/). If your functions pass the `cskit` tests, then you can be reasonably sure that the functions will work on compute.studio.

Compute Studio Kit also provides a helper command for retrieving your [Compute Studio API](https://docs.compute.studio/api/guide/) token.

## Install `cskit`

```bash
pip install cskit
```

## Set up the `csconfig` directory

```bash
$ csk-init
```

## Test your functions

```python
from cskit import FunctionsTest

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

## Get your [Compute Studio API](https://docs.compute.studio/api/guide/) token

```bash
$ csk-token --username myuser --password mypass
Token: your-token-here
```

## Run the tests

```bash
py.test cskit -v
```
