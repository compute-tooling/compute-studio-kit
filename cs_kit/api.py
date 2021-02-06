from io import StringIO
from pathlib import Path
import time
from typing import Optional
import os

import requests
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

    Learn how to get your API token from the Authentication
    `docs <https://docs.compute.studio/api/auth.html>`_. Once you have your token,
    you can save it in a file named ``.cs_api_token`` in the home directory of your
    computer. You can also set it as an environment variable or pass it directly
    to the ``ComputeStudio`` class.
    """

    host = "https://compute.studio"

    def __init__(self, owner: str, title: str, api_token: Optional[str] = None):
        self.owner = owner
        self.title = title
        api_token = self.get_token(api_token)
        self.auth_header = {"Authorization": f"Token {api_token}"}
        self.sim_url = f"{self.host}/{owner}/{title}/api/v1/"
        self.inputs_url = f"{self.host}/{owner}/{title}/api/v1/inputs/"

    def create(self, adjustment: dict = None, meta_parameters: dict = None):
        """
        Create a simulation on Compute Studio.

        Parameters
        ----------
        adjustment : dict
            Parameter values in the paramtools `format <https://paramtools.dev/api/reference.html>`_.

        meta_parameters: dict
            Meta parameters for the simulation in a key:value format.

        Returns
        --------
        resp: dict
            Response from the Compute Studio server. Use this to get the simulation ID and status.
        """
        adjustment = adjustment or {}
        meta_parameters = meta_parameters or {}
        resp = requests.post(
            self.sim_url,
            json={"adjustment": adjustment, "meta_parameters": meta_parameters},
            headers=self.auth_header,
        )
        if resp.status_code == 201:
            data = resp.json()
            pollresp = requests.get(
                f"{self.sim_url}{data['sim']['model_pk']}/edit/",
                headers=self.auth_header,
            )
            polldata = pollresp.json()
            while pollresp.status_code == 200 and polldata["status"] == "PENDING":
                time.sleep(3)
                pollresp = requests.get(
                    f"{self.sim_url}{data['sim']['model_pk']}/edit/",
                    headers=self.auth_header,
                )
                polldata = pollresp.json()
            if pollresp.status_code == 200 and polldata["status"] == "SUCCESS":
                simresp = requests.get(
                    f"{self.sim_url}{data['sim']['model_pk']}/remote/",
                    headers=self.auth_header,
                )
                return simresp.json()
            else:
                raise APIException(pollresp.text)
        raise APIException(resp.text)

    def detail(self, model_pk: int, wait=True, polling_interval=5, timeout=600):
        """
        Get detail for a simulation.

        Parameters
        ----------
        model_pk : int
            ID for the simulation.

        wait: bool
            Meta parameters for the simulation in a key:value format.

        polling_interval: int
            Polling interval dictates how often the status of the results will be checked.

        timeout: int
            Time in seconds to wait for the simulation to finish.

        Returns
        --------
        resp: dict
            Response from the Compute Studio server.

        """
        start = time.time()
        while wait:
            if (time.time() - start) > timeout:
                raise TimeoutError(f"Simulation not ready in under {timeout} seconds.")

            resp = requests.get(f"{self.sim_url}{model_pk}/", headers=self.auth_header)
            if resp.status_code == 202 and wait:
                continue  # waiting on the simulation to finish.
            elif resp.status_code == 202 and not wait:
                return resp.json()
            elif resp.status_code == 200:
                return resp.json()
            else:
                raise APIException(resp.text)

            time.sleep(polling_interval)

    def inputs(self, model_pk: Optional[int] = None):
        """
        Get the inputs for a simulation or retrieve the inputs documentation for the app.

        Parameters
        -----------
        model_pk: int
            Id for the simulation.

        Returns
        -------
        resp: dict
            Response from the Compute Studio server.

        """
        if model_pk is None:
            resp = requests.get(f"{self.sim_url}inputs/", headers=self.auth_header)
            resp.raise_for_status()
            return resp.json()
        else:
            resp = requests.get(
                f"{self.sim_url}{model_pk}/edit/", headers=self.auth_header
            )
            resp.raise_for_status()
            return resp.json()

    def results(self, model_pk):
        """
        Retrieve and parse results into the appropriate data structure. Currently,
        CSV outputs are loaded into a pandas `DataFrame`. Other outputs are returned
        as is.

        Parameters
        ----------
        model_pk: int
            Id for the simulation.


        Returns
        -------
        result: dict
            Dictionary of simulation outputs formated as title:output.
        """
        result = self.detail(model_pk)
        res = {}
        for output in result["outputs"]["downloadable"]:
            if output["media_type"] == "CSV":
                res[output["title"]] = pd.read_csv(StringIO(output["data"]))
            else:
                res[output["title"]] = output["data"]
        return res

    def update(
        self,
        model_pk,
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

        title: str
            Title of the simulation.

        is_public: bool
            Set whether simulation is public or private.

        Notify_on_completion: bool
            Send an email notification when the simulation completes.


        Returns
        -------
        resp: dict
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

        resp = requests.put(
            f"{self.sim_url}{model_pk}/", json=sim_kwargs, headers=self.auth_header,
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            raise APIException(resp.text)

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

