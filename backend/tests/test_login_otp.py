"""Login por OTP: solicitud, verificación, un solo uso, intentos y caducidad."""

from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.models.login_otp import LoginOtp
from app.services import auth_service as mod
from app.services.auth_service import AuthService


class FakeDb:
    def __init__(self) -> None:
        self.rows: dict[str, LoginOtp] = {}
        self.commits = 0

    async def get(self, _model, key):
        return self.rows.get(key)

    def add(self, obj):
        self.rows[obj.email] = obj

    async def flush(self):
        pass

    async def commit(self):
        self.commits += 1

    async def delete(self, obj):
        self.rows.pop(obj.email, None)


@pytest.fixture
def sent(monkeypatch):
    codes: list[tuple[str, str]] = []

    async def fake_send(_settings, to, code):
        codes.append((to, code))

    monkeypatch.setattr(mod, "send_otp", fake_send)

    async def fake_user(self, db, *, email, name, azure_oid, default_role="procesos"):
        return SimpleNamespace(email=email, name=name, role=SimpleNamespace(name="procesos"))

    monkeypatch.setattr(AuthService, "_get_or_create_user", fake_user)
    return codes


def _svc(**kw) -> AuthService:
    return AuthService(Settings(secret_key="x" * 40, _env_file=None, **kw))


@pytest.mark.asyncio
async def test_flujo_completo_y_un_solo_uso(sent):
    db, svc = FakeDb(), _svc()
    await svc.request_otp(db, email="Ana@poligran.edu.co")
    ((to, code),) = sent
    assert to == "ana@poligran.edu.co"

    token, user = await svc.verify_otp(db, email="ana@poligran.edu.co", code=code)
    assert token and user.email == "ana@poligran.edu.co"

    with pytest.raises(HTTPException) as exc:  # reutilizar el código falla
        await svc.verify_otp(db, email="ana@poligran.edu.co", code=code)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_dominio_no_institucional_rechazado(sent):
    with pytest.raises(HTTPException) as exc:
        await _svc().request_otp(FakeDb(), email="x@gmail.com")
    assert exc.value.status_code == 403
    assert not sent


@pytest.mark.asyncio
async def test_correo_fuera_de_lista_no_envia_ni_revela(sent):
    db = FakeDb()
    await _svc(allowed_emails="ok@poligran.edu.co").request_otp(db, email="otro@poligran.edu.co")
    assert not sent and not db.rows


@pytest.mark.asyncio
async def test_codigo_incorrecto_bloquea_tras_max_intentos(sent):
    db, svc = FakeDb(), _svc(otp_max_attempts=3)
    await svc.request_otp(db, email="a@poligran.edu.co")
    ((_, code),) = sent
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(3):
        with pytest.raises(HTTPException):
            await svc.verify_otp(db, email="a@poligran.edu.co", code=wrong)
    assert db.commits == 3
    with pytest.raises(HTTPException):  # el código correcto ya no sirve
        await svc.verify_otp(db, email="a@poligran.edu.co", code=code)


@pytest.mark.asyncio
async def test_codigo_vencido(sent):
    db, svc = FakeDb(), _svc()
    await svc.request_otp(db, email="a@poligran.edu.co")
    ((_, code),) = sent
    db.rows["a@poligran.edu.co"].expires_at = datetime.now(UTC) - timedelta(seconds=1)
    with pytest.raises(HTTPException) as exc:
        await svc.verify_otp(db, email="a@poligran.edu.co", code=code)
    assert exc.value.status_code == 401


@pytest.mark.asyncio
async def test_reenvio_antes_del_cooldown_da_429(sent):
    db, svc = FakeDb(), _svc()
    await svc.request_otp(db, email="a@poligran.edu.co")
    with pytest.raises(HTTPException) as exc:
        await svc.request_otp(db, email="a@poligran.edu.co")
    assert exc.value.status_code == 429
    assert len(sent) == 1
