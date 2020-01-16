# -*- coding: utf-8 -*-
import datetime
import logging
import typing
from urllib.parse import quote, unquote, urlencode, urlparse

import httpx


async def request_helper(url, method, **kwargs):
    async with httpx.Client() as client:
        options = {
            "GET": client.get,
            "POST": client.post,
            "PUT": client.put,
            "DELETE": client.delete,
        }
        if method in ["POST", "PUT"]:
            headers = kwargs.get("headers")
            if headers.get("Content-Type") == "application/json":
                json = kwargs.pop("data", None)
                kwargs.update(json=json)
        return await options[method](url, **kwargs)


class OauthException(Exception):
    pass


class StorageInterface:
    def __init__(
        self,
        refresh_token: str = None,
        access_token: str = None,
        date_added: datetime.datetime = None,
    ):
        self.refresh_token = refresh_token
        self.access_token = access_token
        self.date_added = date_added

    def expiry_config(self):
        """Expiry duration of different token in hours"""
        return {"access_token": 1, "refresh_token": 100 * 24}

    def has_expired(self, kind="access_token"):
        if self.date_added.tzinfo:
            self.date_added = self.date_added.replace(tzinfo=None)
        timestamp = datetime.datetime.now() - self.date_added
        in_hours = timestamp.total_seconds() / 3600
        return in_hours > self.expiry_config()[kind]

    async def save_token(self, **token):
        self.access_token = token["access_token"]
        self.refresh_token = token["refresh_token"]
        self.date_added = datetime.datetime.now()

    async def get_token(self, view_url, condition: typing.Callable = lambda: True):
        if not condition() and not self.access_token:
            raise OauthException(
                ("Token not available, " "please visit the {} url.").format(view_url)
            )
        if self.date_added:
            self.date_added = self.date_added.replace(tzinfo=None)
        return self


class AccountingOauth:
    def __init__(
        self,
        redirect_uri: str,
        client_id: str,
        client_secret: str,
        scopes: typing.List[str],
        token_base_url: str,
        auth_base_url: str,
        button_image="https://files.beesama.now.sh/C2QB_green_btn_med_default.png",
        state="app-server",
        storage_interface: StorageInterface = None,
        remove_redirect_uri_on_token_refresh=False,
        **kwargs,
    ):
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self.button_image = button_image
        self.state = state
        self.auth_base_url = auth_base_url
        self.token_base_url = token_base_url
        self.scopes = scopes
        self.kwargs = kwargs
        self.interface = storage_interface
        self.remove_redirect_uri_on_token_refresh = remove_redirect_uri_on_token_refresh

    def auth_params(self) -> typing.Dict[str, typing.Any]:
        result = {
            "redirect_uri": self.redirect_uri,
            "client_id": self.client_id,
            "response_type": "code",
            "scope": quote(" ".join(self.scopes)),
            **self.kwargs,
        }
        if self.state:
            result["state"] = self.state
        return result

    def get_authorization_url(self):
        params = unquote(urlencode(self.auth_params()))
        return "{}?{}".format(self.auth_base_url, params)

    def auth_button(self):
        """Create an html button that includes the authorization url"""
        return """<a href="{}"><img src="{}"/></a>""".format(
            self.get_authorization_url(), self.button_image
        )

    def token_params(self, key):
        """Different post params for either authorize or refresh"""
        return {}

    def token_header_params(self):
        return {"Content-type": "application/json"}

    async def _get_token_details(self, grant_type, param):
        options = {
            "authorize": ("authorization_code", "code"),
            "refresh": ("refresh_token", "refresh_token"),
        }
        data = options[grant_type]
        params = {
            "grant_type": data[0],
            "redirect_uri": self.redirect_uri,
            data[1]: param,
            **self.token_params(grant_type),
        }
        if self.remove_redirect_uri_on_token_refresh:
            if data[0] == "refresh_token":
                params.pop("redirect_uri")
        headers = self.token_header_params()
        response = await request_helper(
            self.token_base_url, "POST", data=params, headers=headers
        )
        if response.status_code >= 400:
            print(response.json())
            print(params)
            response.raise_for_status()
        return response.json(), response.status_code

    async def get_token(self, code):
        return await self._get_token_details("authorize", code)

    async def refresh_token(self, refresh_token):
        return await self._get_token_details("refresh", refresh_token)

    async def on_auth_response(self, state=None, **kwargs):
        if state != self.state:
            raise OauthException("Invalid state sent on response")
        response = {**kwargs}
        token_response, status = await self.get_token(kwargs["code"])
        if status < 400:
            await self.interface.save_token(**kwargs, **token_response)
        token_response.update(status=status)
        return token_response
