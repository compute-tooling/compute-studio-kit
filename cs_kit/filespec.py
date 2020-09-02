import json

from fsspec.spec import AbstractFileSystem
from fsspec.registry import register_implementation
from fsspec.utils import infer_storage_options
from fsspec.implementations.memory import MemoryFile
import requests


class CSFileSystem(AbstractFileSystem):
    """
    Interface to data on Compute Studio

    When using fsspec.open, allows URIs of the form:

    - cs://owner:title@model-pk/ : get meta data for simulation
    - cs://owner:title@model-pk/inputs : get inputs metadata for simulation
    - cs://owner:title@model-pk/inputs/adjustment : get full adjustment
    - cs://owner:title@model-pk/input/adjustment/section : get specific section of adjustment
    - cs://owner:title@model-pk/input/meta_parameters : get meta_parameters
    - cs://owner:title@model-pk/outputs : get outputs from reform
    - cs://owner:title@model-pk/owner : get owner of simulation
    - cs://owner:title@model-pk/title : get title of simulation

    For authorised access, you must provide an API Token, which can be made
    at https://docs.compute.studio/api/auth/. The API Token can be specified like:

    with fsspec.open("cs://PSLmodels:Tax-Brain@1234", api_token=api_token) as f:
        result = f.read()

    Modified version of the GitHub fsspec implementation:
    - https://filesystem-spec.readthedocs.io/en/latest/api.html#id0
    """

    url = "https://compute.studio/{owner}/{title}/api/v1/{model_pk}/"
    protocol = "cs"

    def __init__(
        self,
        owner,
        title,
        model_pk,
        resource=None,
        field=None,
        section=None,
        api_token=None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.owner = owner
        self.title = title
        self.model_pk = model_pk
        self.resource = resource
        self.field = field
        self.section = section
        self.api_token = api_token

    @classmethod
    def _strip_protocol(cls, path):
        opts = infer_storage_options(path)
        if "username" not in opts:
            return super()._strip_protocol(path)
        return opts["path"].lstrip("/")

    @staticmethod
    def _get_kwargs_from_urls(path):
        opts = infer_storage_options(path)
        out = {"owner": opts["username"], "title": opts["password"]}
        if opts["host"]:
            out["model_pk"] = opts["host"]

        path = opts["path"]
        if len(path) > 0:
            parts = path[1:].split("/")
        else:
            parts = []

        if len(parts) > 0 and parts[0] in ("inputs", "outputs", "owner", "title"):
            out["resource"] = parts[0]

        if len(parts) > 1 and parts[1] in ("adjustment", "meta_parameters", "title"):
            out["field"] = parts[1]

        if len(parts) > 2 and parts[1] == "adjustment":
            out["section"] = parts[2]

        return out

    def _open(self, path, mode="rb", block_size=None, **kwargs):
        if mode != "rb":
            raise NotImplementedError
        base_url = self.url.format(
            owner=self.owner, title=self.title, model_pk=self.model_pk,
        )

        if self.resource == "inputs":
            url = base_url + "edit/"
        elif self.resource is None:
            url = base_url + "remote/"
        else:
            url = base_url

        if self.api_token is not None:
            headers = {"Authorization": f"Token {self.api_token}"}
        else:
            headers = None

        r = requests.get(url, headers=headers)
        if r.status_code == 404:
            raise FileNotFoundError(path)
        r.raise_for_status()

        data = r.json()
        if self.resource == "inputs" and self.field is None:
            result = data
        elif self.resource == "inputs" and self.field != "adjustment":
            result = data[self.field]
        elif self.resource == "inputs" and self.field == "adjustment":
            result = data[self.field]
            if self.section is not None:
                result = result[self.section]
        elif self.resource == "outputs":
            result = data["outputs"]["downloadable"]
        elif self.resource in ("title", "owner"):
            result = {self.resource: data[self.resource]}
        elif self.resource is None:
            result = dict(data, outputs=base_url)
        else:
            raise FileNotFoundError()
        return MemoryFile(None, None, json.dumps(result).encode("utf-8"))


register_implementation("cs", CSFileSystem)
