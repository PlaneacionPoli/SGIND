"""Login Microsoft multi-tenant: state firmado, dominio institucional y rechazo del consentimiento."""

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.core.security import create_access_token
from app.services.auth_service import AuthService


def _svc(**kw) -> AuthService:
    return AuthService(
        Settings(
            secret_key="x" * 40,
            azure_tenant_id="organizations",
            azure_client_id="cid",
            _env_file=None,
            **kw,
        )
    )


def test_state_generado_es_valido():
    svc = _svc()
    url = svc.get_login_url()
    assert "login.microsoftonline.com/organizations" in url
    state = url.split("state=")[1].split("&")[0]
    svc.verify_state(state)  # no lanza


@pytest.mark.parametrize("state", [None, "", "sgind", "basura.basura.basura"])
def test_state_invalido_rechazado(state):
    with pytest.raises(HTTPException):
        _svc().verify_state(state)


def test_jwt_de_sesion_no_sirve_como_state():
    svc = _svc()
    token = create_access_token(
        "a@poligran.edu.co", settings=svc.settings, extra={"role": "procesos"}
    )
    with pytest.raises(HTTPException) as exc:
        svc.verify_state(token)
    assert exc.value.status_code == 400


@pytest.mark.asyncio
async def test_callback_con_error_redirige_a_login(client):
    resp = await client.get("/api/v1/auth/callback?error=access_denied", follow_redirects=False)
    assert resp.status_code in (302, 307)
    assert resp.headers["location"].endswith("/login?error=access_denied")


@pytest.mark.asyncio
async def test_callback_rechaza_dominio_ajeno(monkeypatch):
    svc = _svc()

    class FakeMsal:
        def acquire_token_by_authorization_code(self, **_):
            return {"access_token": "t"}

    svc._msal_app = FakeMsal()

    class FakeResp:
        def raise_for_status(self): ...
        def json(self):
            return {"mail": "intruso@otra-universidad.edu", "displayName": "X", "id": "1"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a): ...
        async def get(self, *a, **k):
            return FakeResp()

    monkeypatch.setattr("app.services.auth_service.httpx.AsyncClient", lambda: FakeClient())
    with pytest.raises(HTTPException) as exc:
        await svc.handle_callback("code", db=None)
    assert exc.value.status_code == 403
