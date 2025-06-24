import pytest
from httpx import AsyncClient
from ..app.main import app # 使用相對導入

# Pytest 夾具，用於在測試中啟動 FastAPI 應用
@pytest.fixture(scope="module")
async def async_client():
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
async def test_sql_injection_defense_product_search(async_client):
    """測試 Laravel API 搜尋產品的 SQL 防禦"""
    response = await async_client.post(
        "/attack/simulate_sql_injection",
        json={
            "target_endpoint": "/products/search",
            "payload": "' OR 1=1 --", # SQL 注入 payload
            "expected_status": 200 # 預期 Laravel 會成功處理請求並防禦注入
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    # 斷言響應內容不包含常見的 SQL 錯誤信息
    assert "SQLSTATE" not in response.json()["response"]
    assert "syntax error" not in response.json()["response"]
    assert "成功防禦 SQL 注入" in response.json()["message"]

@pytest.mark.asyncio
async def test_xss_defense_comments(async_client):
    """測試 Laravel API 評論提交的 XSS 防禦"""
    # 1. 模擬登入以獲取有效的 Sanctum token
    login_response = await async_client.post(
        "/attack/simulate_login",
        json={
            "target_endpoint": "/login",
            "payload": '{"email": "test@example.com", "password": "password"}',
            "expected_status": 200
        }
    )
    assert login_response.status_code == 200
    assert login_response.json()["status"] == "success"
    token = login_response.json()["response"]["token"]
    assert token is not None

    # 2. 使用獲取的 token 模擬提交帶有 XSS payload 的評論
    xss_payload_content = "<script>alert('XSSed!')</script>"
    response = await async_client.post(
        "/attack/simulate_xss",
        json={
            "target_endpoint": "/comments",
            "payload": xss_payload_content,
            "expected_status": 201, # 預期評論成功提交
            "headers": {"Authorization": f"Bearer {token}"}
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    # 斷言原始的 XSS payload 不在響應中 (已被轉義)
    assert xss_payload_content not in response.json()["response"]
    # 斷言轉義後的 HTML 實體存在於響應中
    assert "&lt;script&gt;alert(&quot;XSSed!&quot;)&lt;/script&gt;" in response.json()["response"]
    assert "成功防禦 XSS" in response.json()["message"]

@pytest.mark.asyncio
async def test_broken_auth_invalid_token(async_client):
    """測試 Laravel API 使用無效 JWT token 訪問受保護端點"""
    response = await async_client.post(
        "/attack/simulate_broken_auth",
        json={
            "target_endpoint": "/user",
            "payload": "invalid.jwt.token", # 無效的 token
            "expected_status": 401 # 預期返回 401 Unauthorized
        }
    )
    assert response.status_code == 200 # FastAPI 模擬器本身的狀態碼
    assert response.json()["status"] == "success"
    assert "401" in response.json()["message"] # 檢查 Laravel 返回的 401 狀態碼信息
    assert "Unauthenticated" in response.json()["response"]

@pytest.mark.asyncio
async def test_broken_auth_no_token(async_client):
    """測試 Laravel API 在沒有提供 token 的情況下訪問受保護端點"""
    response = await async_client.post(
        "/attack/simulate_broken_auth",
        json={
            "target_endpoint": "/user",
            "payload": "", # 不提供 token
            "expected_status": 401 # 預期返回 401 Unauthorized
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "401" in response.json()["message"]
    assert "Unauthenticated" in response.json()["response"]

@pytest.mark.asyncio
async def test_successful_login(async_client):
    """測試 Laravel API 成功登入並獲取 token"""
    response = await async_client.post(
        "/attack/simulate_login",
        json={
            "target_endpoint": "/login",
            "payload": '{"email": "test@example.com", "password": "password"}',
            "expected_status": 200
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert "Login successful" in response.json()["message"]
    assert "token" in response.json()["response"] # 斷言響應中包含 token
    assert response.json()["response"]["token"] is not None

@pytest.mark.asyncio
async def test_failed_login_invalid_credentials(async_client):
    """測試 Laravel API 無效憑證登入失敗"""
    response = await async_client.post(
        "/attack/simulate_login",
        json={
            "target_endpoint": "/login",
            "payload": '{"email": "test@example.com", "password": "wrong_password"}',
            "expected_status": 401 # 預期登入失敗返回 401
        }
    )
    assert response.status_code == 200
    assert response.json()["status"] == "failed"
    assert "Invalid credentials" in response.json()["response"]
