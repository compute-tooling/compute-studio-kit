from io import StringIO
import time
import os

import requests
import pandas as pd


class APIException(Exception):
    pass


class ComputeStudio:
    host = "https://compute.studio"

    def __init__(self, owner, title, api_token=None):
        self.owner = owner
        self.title = title
        api_token = self.get_token(api_token)
        self.auth_header = {"Authorization": f"Token {api_token}"}
        self.sim_url = f"{self.host}/{owner}/{title}/api/v1/"
        self.inputs_url = f"{self.host}/{owner}/{title}/api/v1/inputs/"

    def create(self, adjustment: dict = None, meta_parameters: dict = None):
        adjustment = adjustment or {}
        meta_parameters = meta_parameters or {}
        resp = requests.post(
            self.sim_url,
            json={"adjustment": adjustment, "meta_parameters": meta_parameters},
            headers=self.auth_header,
        )
        if resp.status_code == 201:
            data = resp.json()
            pollresp = requests.get(f"{self.inputs_url}{data['hashid']}/")
            polldata = pollresp.json()
            while pollresp.status_code == 200 and polldata["status"] == "PENDING":
                time.sleep(3)
                pollresp = requests.get(f"{self.inputs_url}{data['hashid']}/")
                polldata = pollresp.json()
            if pollresp.status_code == 200 and polldata["status"] == "SUCCESS":
                return polldata
            else:
                raise APIException(pollresp.text)
        raise APIException(resp.text)

    def detail(self, model_pk):
        while True:
            resp = requests.get(f"{self.sim_url}{model_pk}/")
            if resp.status_code == 202:
                pass
            elif resp.status_code == 200:
                return resp.json()
            else:
                raise APIException(resp.text)
            time.sleep(5)

    def results(self, model_pk):
        result = self.detail(model_pk)
        res = {}
        for output in result["outputs"]["downloadable"]:
            if output["media_type"] == "CSV":
                res[output["title"]] = pd.read_csv(StringIO(output["data"]))
            else:
                print(f'{output["media_type"]} not implemented yet')
        return res

    def get_token(self, api_token):
        if api_token:
            return api_token
        elif os.environ.get("CS_API_TOKEN", None) is not None:
            return os.environ["CS_API_TOKEN"]
        elif os.path.exists("~/.cs-api-token"):
            with open("~/.cs-api-token", "r") as f:
                return f.read().strip()
        else:
            raise APIException(
                "API token not found. It can be passed as an argument to "
                "this class, as an environment variable at CS_API_TOKEN, "
                "or read from ~/.cs-api-token"
            )
