import pytest

@pytest.mark.asyncio
async def test_tp_4_1_health(client):
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_tp_4_2_dashboard_kpis_sin_auth(client):
    response = await client.get("/api/v1/dashboard/kpis")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_tp_4_3_post_om_procesos_forbidden(client, auth_as_procesos):
    payload = {
        "id_indicador": "TEST-API",
        "nombre_indicador": "Test",
        "periodo": "Enero",
        "anio": 2025,
        "tiene_om": 1,
    }
    response = await client.post("/api/v1/om", json=payload)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_tp_4_4_get_indicators_con_auth(client, auth_as_calidad):
    response = await client.get("/api/v1/indicators", params={"limit": 5})
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "items" in data
    assert isinstance(data["items"], list)


@pytest.mark.asyncio
async def test_tp_4_5_indicators_filtro_anio(client, auth_as_calidad):
    response = await client.get("/api/v1/indicators", params={"anio": 2025, "limit": 3})
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 0


@pytest.mark.asyncio
async def test_cmi_estrategico(client, auth_as_calidad):
    response = await client.get("/api/v1/cmi/estrategico")
    assert response.status_code == 200
    data = response.json()
    assert "lineas" in data


@pytest.mark.asyncio
async def test_dashboard_semaphore(client, auth_as_calidad):
    response = await client.get("/api/v1/dashboard/semaphore")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
