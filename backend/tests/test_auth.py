import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_register_returns_token(async_client: AsyncClient):
    response = await async_client.post(
        "/auth/register",
        json={"email": "test@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(async_client: AsyncClient):
    payload = {"email": "dup@example.com", "password": "StrongPass123!"}
    await async_client.post("/auth/register", json=payload)
    response = await async_client.post("/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_valid_credentials(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "login@example.com", "password": "StrongPass123!"},
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "login@example.com", "password": "StrongPass123!"},
    )
    assert response.status_code == 200
    assert "access_token" in response.json()


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(async_client: AsyncClient):
    await async_client.post(
        "/auth/register",
        json={"email": "wrong@example.com", "password": "StrongPass123!"},
    )
    response = await async_client.post(
        "/auth/login",
        json={"email": "wrong@example.com", "password": "WrongPass!"},
    )
    assert response.status_code == 401
