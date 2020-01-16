import pytest
import datetime
from accounting_oauth import AccountingOauth, StorageInterface


@pytest.fixture
def q_client(quickbook_client):
    return quickbook_client(StorageInterface())


@pytest.mark.asyncio
async def test_authorization(q_client: AccountingOauth, mock_request, mocker):
    mock_httpx = mocker.patch("accounting_oauth.oauth.request_helper")
    mock_httpx.return_value = mock_request(
        {
            "access_token": "eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..Jf3JsITu2P6GE4ufb6ElYA.0ZSTcoePtEMg5xHda7RjuMtPFIY93MsC-CU8fjK8kZJRBtYVgX1vCUpeK6IqI6f6QD3DMuzaHDSLWuH4gqXmEsYniYizLQ4eQJwFHyxhiF9jYC_SV7yPd4yUoG1DrhirU0Ujy_Dw02vkMXIJSOEAg4HUWg1CmNEKTvTWn4X5LutJeIt8A2FsSU-Dinlg32HUfftT87GMz7_2IE_do4gfqhQsH2aRIE26n7OPql153JJEgjH-FeCJ6_ZjWbD8T5ZAmDB9MO7xvvqQR8a6Vh9b3ukZ3CqbL7KaejxxiZGM6sGmimT9fhoeaIgVNX5S6x3oDIfZNKtmHiyswOsd_p5aj00tjbBdgQxgasp_Z7TTqzxg04RtS3jgtwIaaApbP3yp-UCTneUU0sL01znql8MUbNL4EXmegBEUtBD_El_C7wr7RAWpNLEwv9pw1hJT9fuXUyxA6P9fwL_I6HCnZDvrer6oCc7-POVQ8kXXE9eMQ1-70AA8-l6vRxj6Pj8xny2_lUWnvZJWxvInQ6aJQGT6tDHaAh60Ipd4P6b6UC2Qtyo6Ld4GQWYnRU4i_VEq32ciY7jYyyelDV-CnWdM2W6CcpTZg8lMVzM5QdoNMerySjzSsadk9q0gmseGCJkkgBi1kxNERam_xXN3urvg0w4HU0lria1nEk0kMlEMPD7XthvWQ4HXAXjT1aRa-YoLukkb.XNZBgw0xILTZylda_g4S3Q",
            "expires_in": 3600,
            "refresh_token": "Q011532713322Pgork3wPLnNTwNOPXsYpvBU8rrkW4W8jNYa8O",
            "token_type": "bearer",
            "x_refresh_token_expires_in": 8721585,
        }
    )
    authorization_response = {
        "code": "the developer is here",
        "state": q_client.state,
        "realmId": "1234",
    }
    assert q_client.interface.access_token == None
    await q_client.on_auth_response(**authorization_response)
    assert_get_token(mock_httpx, authorization_response["code"])
    assert (
        q_client.interface.access_token
        == "eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..Jf3JsITu2P6GE4ufb6ElYA.0ZSTcoePtEMg5xHda7RjuMtPFIY93MsC-CU8fjK8kZJRBtYVgX1vCUpeK6IqI6f6QD3DMuzaHDSLWuH4gqXmEsYniYizLQ4eQJwFHyxhiF9jYC_SV7yPd4yUoG1DrhirU0Ujy_Dw02vkMXIJSOEAg4HUWg1CmNEKTvTWn4X5LutJeIt8A2FsSU-Dinlg32HUfftT87GMz7_2IE_do4gfqhQsH2aRIE26n7OPql153JJEgjH-FeCJ6_ZjWbD8T5ZAmDB9MO7xvvqQR8a6Vh9b3ukZ3CqbL7KaejxxiZGM6sGmimT9fhoeaIgVNX5S6x3oDIfZNKtmHiyswOsd_p5aj00tjbBdgQxgasp_Z7TTqzxg04RtS3jgtwIaaApbP3yp-UCTneUU0sL01znql8MUbNL4EXmegBEUtBD_El_C7wr7RAWpNLEwv9pw1hJT9fuXUyxA6P9fwL_I6HCnZDvrer6oCc7-POVQ8kXXE9eMQ1-70AA8-l6vRxj6Pj8xny2_lUWnvZJWxvInQ6aJQGT6tDHaAh60Ipd4P6b6UC2Qtyo6Ld4GQWYnRU4i_VEq32ciY7jYyyelDV-CnWdM2W6CcpTZg8lMVzM5QdoNMerySjzSsadk9q0gmseGCJkkgBi1kxNERam_xXN3urvg0w4HU0lria1nEk0kMlEMPD7XthvWQ4HXAXjT1aRa-YoLukkb.XNZBgw0xILTZylda_g4S3Q"
    )
    assert (
        q_client.interface.refresh_token
        == "Q011532713322Pgork3wPLnNTwNOPXsYpvBU8rrkW4W8jNYa8O"
    )


def assert_get_token(mock_post, code):
    mock_post.assert_called_with(
        "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        "POST",
        data={
            "grant_type": "authorization_code",
            "redirect_uri": "http://testserver/quickbooks/auth-response",
            "code": code,
        },
        headers={},
    )


def assert_refresh_token(mock_post, refresh_token):
    mock_post.assert_called_with(
        "https://oauth.platform.intuit.com/oauth2/v1/tokens/bearer",
        "POST",
        data={"grant_type": "refresh_token", "refresh_token": refresh_token},
        headers={},
    )


@pytest.mark.asyncio
async def test_refreshing_token_that_has_expired(
    quickbook_client: AccountingOauth, mock_request, mocker
):
    q_client = quickbook_client(
        StorageInterface(
            refresh_token="Q011532713322Pgork3wPLnNTwNOPXsYpvBU8rrkW4W8jNYa8O",
            access_token="eyJlbmMiOiJBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..Jf3JsITu2P6GE4ufb6ElYA.0ZSTcoePtEMg5xHda7RjuMtPFIY93MsC-CU8fjK8kZJRBtYVgX1vCUpeK6IqI6f6QD3DMuzaHDSLWuH4gqXmEsYniYizLQ4eQJwFHyxhiF9jYC_SV7yPd4yUoG1DrhirU0Ujy_Dw02vkMXIJSOEAg4HUWg1CmNEKTvTWn4X5LutJeIt8A2FsSU-Dinlg32HUfftT87GMz7_2IE_do4gfqhQsH2aRIE26n7OPql153JJEgjH-FeCJ6_ZjWbD8T5ZAmDB9MO7xvvqQR8a6Vh9b3ukZ3CqbL7KaejxxiZGM6sGmimT9fhoeaIgVNX5S6x3oDIfZNKtmHiyswOsd_p5aj00tjbBdgQxgasp_Z7TTqzxg04RtS3jgtwIaaApbP3yp-UCTneUU0sL01znql8MUbNL4EXmegBEUtBD_El_C7wr7RAWpNLEwv9pw1hJT9fuXUyxA6P9fwL_I6HCnZDvrer6oCc7-POVQ8kXXE9eMQ1-70AA8-l6vRxj6Pj8xny2_lUWnvZJWxvInQ6aJQGT6tDHaAh60Ipd4P6b6UC2Qtyo6Ld4GQWYnRU4i_VEq32ciY7jYyyelDV-CnWdM2W6CcpTZg8lMVzM5QdoNMerySjzSsadk9q0gmseGCJkkgBi1kxNERam_xXN3urvg0w4HU0lria1nEk0kMlEMPD7XthvWQ4HXAXjT1aRa-YoLukkb.XNZBgw0xILTZylda_g4S3Q",
            date_added=datetime.datetime(2019, 5, 10),  # access token has expired
        )
    )
    mock_httpx = mocker.patch("accounting_oauth.oauth.request_helper")
    result_token = "eyJlbmMiOiTBMTI4Q0JDLUhTMjU2IiwiYWxnIjoiZGlyIn0..Jf3JsITu2P6GE4ufb6ElYA.0ZSTcoePtEMg5xHda7RjuMtPFIY93MsC-CU8fjK8kZJRBtYVgX1vCUpeK6IqI6f6QD3DMuzaHDSLWuH4gqXmEsYniYizLQ4eQJwFHyxhiF9jYC_SV7yPd4yUoG1DrhirU0Ujy_Dw02vkMXIJSOEAg4HUWg1CmNEKTvTWn4X5LutJeIt8A2FsSU-Dinlg32HUfftT87GMz7_2IE_do4gfqhQsH2aRIE26n7OPql153JJEgjH-FeCJ6_ZjWbD8T5ZAmDB9MO7xvvqQR8a6Vh9b3ukZ3CqbL7KaejxxiZGM6sGmimT9fhoeaIgVNX5S6x3oDIfZNKtmHiyswOsd_p5aj00tjbBdgQxgasp_Z7TTqzxg04RtS3jgtwIaaApbP3yp-UCTneUU0sL01znql8MUbNL4EXmegBEUtBD_El_C7wr7RAWpNLEwv9pw1hJT9fuXUyxA6P9fwL_I6HCnZDvrer6oCc7-POVQ8kXXE9eMQ1-70AA8-l6vRxj6Pj8xny2_lUWnvZJWxvInQ6aJQGT6tDHaAh60Ipd4P6b6UC2Qtyo6Ld4GQWYnRU4i_VEq32ciY7jYyyelDV-CnWdM2W6CcpTZg8lMVzM5QdoNMerySjzSsadk9q0gmseGCJkkgBi1kxNERam_xXN3urvg0w4HU0lria1nEk0kMlEMPD7XthvWQ4HXAXjT1aRa-YoLukkb.XNZBgw0xILTZylda_g4S3Q"
    mock_httpx.return_value = mock_request(
        {
            "access_token": result_token,
            "expires_in": 3600,
            "refresh_token": "Q011532713322Pgork3wPLnNTwNOPXsYpvBU8rrkW4W8jNYa8O",
            "token_type": "bearer",
            "x_refresh_token_expires_in": 8721585,
        }
    )
    assert q_client.interface.has_expired()
    result, error = await q_client.refresh_token(q_client.interface.refresh_token)
    # save token
    await q_client.interface.save_token(**result)
    assert_refresh_token(mock_httpx, q_client.interface.refresh_token)
    assert result["access_token"] == result_token
    assert not q_client.interface.has_expired()
