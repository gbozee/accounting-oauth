import os
import pytest
from accounting_oauth import AccountingOauth
import asyncio


@pytest.fixture
def quickbook_client():
    env = os.getenv

    def init_quickbooks(storage_interface):
        return AccountingOauth(
            redirect_uri="http://testserver/quickbooks/auth-response",
            client_id=env("QUICKBOOKS_CLIENT_ID"),
            client_secret=env("QUICKBOOKS_CLIENT_SECRET"),
            storage_interface=storage_interface,
            scopes=["com.intuit.quickbooks.accounting"],
            token_base_url="https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
            auth_base_url="https://appcenter.intuit.com/connect/oauth2",
            remove_redirect_uri_on_token_refresh=True,
        )

    return init_quickbooks


@pytest.fixture
def create_future():
    def _create_future(value):
        dd = asyncio.Future()
        dd.set_result(value)
        return dd

    return _create_future


@pytest.fixture
def mock_request(create_future):
    def _mock_request(data, status_code=200, as_future=True):
        mck = MockRequst(data, status_code=status_code)
        if as_future:
            return create_future(mck)
        return mck

    return _mock_request


class MockRequst(object):
    def __init__(self, response, **kwargs):
        self.response = response
        self.overwrite = True
        if kwargs.get("overwrite"):
            self.overwrite = True
        self.status_code = kwargs.get("status_code", 200)

    @classmethod
    def raise_for_status(cls):
        pass

    def json(self):
        if self.overwrite:
            return self.response
        return {"data": self.response}

    @property
    def text(self):
        return self.response
