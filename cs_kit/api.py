import asyncio
from functools import wraps
from io import StringIO
import json
from pathlib import Path
import time
from typing import Optional
import os

import httpx
import pandas as pd

from cs_kit.exceptions import APIException


class ComputeStudio:
    """
    Python client for the ComputeStudio webapp.

    - Run simulations
    - Update simulation metadata
    - Download your results


    .. code-block:: python

        client = ComputeStudio("PSLmodels", "TaxBrain")
        client.create()

    Learn how to get your API token from the
    `Authentication docs <https://docs.compute.studio/api/auth.html>`_. Once you have your token,
    you can save it in a file named ``.cs_api_token`` in the home directory of your
    computer. You can also set it as an environment variable or pass it directly
    to the ``ComputeStudio`` class.
    """

    host = "https://compute.studio"

    def __init__(
        self,
        owner: str,
        title: str,
        api_token: Optional[str] = None,
        token_type: Optiona[str] = "Token",
        asynchronous: Optional[bool] = False,
    ):
        self.owner = owner
        self.title = title
        self.asynchronous = asynchronous
        api_token = self.get_token(api_token)
        self.auth_header = {"Authorization": f"{token_type} {api_token}"}
        self.sim_url = f"{self.host}/{owner}/{title}/api/v1/"
        self.inputs_url = f"{self.host}/{owner}/{title}/api/v1/inputs/"

    async def get_inputs_status(self, model_pk):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.sim_url}{model_pk}/edit/", headers=self.auth_header,
            )
        if response.status_code in (200, 400):
            data = response.json()
            return data["status"], data

        response.raise_for_status()

    async def poll_is_valid(self, model_pk):
        inputs_status, data = await self.get_inputs_status(model_pk)
        while inputs_status == "PENDING":
            time.sleep(3)
            inputs_status, data = await self.get_inputs_status(model_pk)
        if inputs_status == "SUCCESS":
            async with httpx.AsyncClient() as client:
                simresp = await client.get(
                    f"{self.sim_url}{model_pk}/remote/", headers=self.auth_header,
                )
                return simresp.json()
        else:
            errors = data.get("errors_warnings")
            traceback = data.get("traceback")
            raise APIException(
                errors or traceback or data, owner=self.owner, title=self.title
            )

    async def create(
        self,
        adjustment: dict = None,
        meta_parameters: dict = None,
        check_is_valid: bool = True,
    ):
        """
        Create a simulation on Compute Studio.

        Parameters
        ----------
        adjustment : dict
            Parameter values in the `ParamTools format <https://paramtools.dev/api/reference.html>`_.

        meta_parameters: dict
            Meta parameters for the simulation in a ``key:value`` format.

        check_is_valid: bool
            Check if inputs are valid before returning.

        Returns
        --------
        response: dict
            Response from the Compute Studio server. Use this to get the simulation ID and status.
        """
        adjustment = adjustment or {}
        meta_parameters = meta_parameters or {}

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.sim_url,
                json={"adjustment": adjustment, "meta_parameters": meta_parameters},
                headers=self.auth_header,
            )
        if resp.status_code == 201:
            data = resp.json()
            model_pk = data["sim"]["model_pk"]
            if check_is_valid:
                return await self.poll_is_valid(model_pk)
            else:
                return await self.detail(model_pk, include_outputs=False, wait=False)

        raise APIException(resp.json())

    async def detail(
        self,
        model_pk: int,
        include_outputs: bool = False,
        wait: bool = True,
        polling_interval: int = 5,
        timeout: int = 600,
    ):
        """
        Get detail for a simulation.

        Parameters
        ----------
        model_pk : int
            ID for the simulation.

        include_outputs: bool
            Include outputs from the simulation in addition to the simulation metadata.

        wait: bool
            Meta parameters for the simulation in a key:value format.

        polling_interval: int
            Polling interval dictates how often the status of the results will be checked.

        timeout: int
            Time in seconds to wait for the simulation to finish.

        Returns
        --------
        response: dict
            Response from the Compute Studio server.

        """
        if include_outputs:
            url = f"{self.sim_url}{model_pk}/"
        else:
            url = f"{self.sim_url}{model_pk}/remote/"

        start = time.time()
        while True:
            if (time.time() - start) > timeout:
                raise TimeoutError(f"Simulation not ready in under {timeout} seconds.")

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, headers=self.auth_header)

            if resp.status_code == 202 and wait:
                continue  # waiting on the simulation to finish.
            elif resp.status_code == 202 and not wait:
                return resp.json()
            elif resp.status_code == 200:
                return resp.json()
            else:
                raise APIException(resp.json())

            time.sleep(polling_interval)

    async def inputs(self, model_pk: Optional[int] = None):
        """
        Get the inputs for a simulation or retrieve the inputs documentation for the app.

        Parameters
        -----------
        model_pk: int
            ID for the simulation.

        Returns
        -------
        response: dict
            Response from the Compute Studio server.

        """
        if model_pk is None:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.sim_url}inputs/", headers=self.auth_header
                )
            resp.raise_for_status()
            return resp.json()
        else:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self.sim_url}{model_pk}/edit/", headers=self.auth_header
                )
            resp.raise_for_status()
            return resp.json()

    async def results(self, model_pk: int, timeout: int = 600):
        """
        Retrieve and parse results into the appropriate data structure. Currently,
        CSV outputs are loaded into a pandas `DataFrame`. Other outputs are returned
        as is.

        Parameters
        ----------
        model_pk: int
            ID for the simulation.

        timeout: int
            Time in seconds to wait for the simulation to finish.

        Returns
        -------
        result: dict
            Dictionary of simulation outputs formated as title:output.
        """
        result = await self.detail(
            model_pk, include_outputs=True, wait=True, timeout=timeout,
        )
        res = {}
        for output in result["outputs"]["downloadable"]:
            if output["media_type"] == "CSV":
                res[output["title"]] = pd.read_csv(StringIO(output["data"]))
            else:
                res[output["title"]] = output["data"]
        return res

    def update(
        self,
        model_pk: int,
        title: Optional[str] = None,
        is_public: Optional[bool] = None,
        notify_on_completion: Optional[bool] = None,
    ):
        """
        Update meta data about a simulation.

        .. code-block:: python

            cs.update(
                model_pk=123,
                title="hello world",
                is_public=True,
                notify_on_completion=True
            )

        Parameters
        ----------
        model_pk: int
            ID for the simulation.

        title: str
            Title of the simulation.

        is_public: bool
            Set whether simulation is public or private.

        Notify_on_completion: bool
            Send an email notification when the simulation completes.


        Returns
        -------
        response: dict
            Response from the Compute Studio server.

        """
        vals = [
            ("title", title),
            ("is_public", is_public),
            ("notify_on_completion", notify_on_completion),
        ]
        sim_kwargs = {}
        for name, val in vals:
            if val is not None:
                sim_kwargs[name] = val

        resp = httpx.put(
            f"{self.sim_url}{model_pk}/", json=sim_kwargs, headers=self.auth_header,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise APIException(resp.json())

    def get_token(self, api_token):
        """Retrieve the API token"""
        token_file_path = Path.home() / ".cs-api-token"
        if api_token:
            return api_token
        elif os.environ.get("CS_API_TOKEN", None) is not None:
            return os.environ["CS_API_TOKEN"]
        elif token_file_path.exists():
            with open(token_file_path, "r") as f:
                return f.read().strip()
        else:
            raise APIException(
                f"API token not found. It can be passed as an argument to "
                f"this class, as an environment variable at CS_API_TOKEN, "
                f"or read from {token_file_path}"
            )
