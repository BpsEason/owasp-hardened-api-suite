from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import asyncio
import json

router = APIRouter()

LARAVEL_API_BASE_URL = "http://nginx:80/api" # 指向 Docker 網絡中的 Nginx 服務

class AttackPayload(BaseModel):
    target_endpoint: str
    payload: str
    expected_status: int = 200
    headers: dict = {}

@router.post("/simulate_sql_injection")
async def simulate_sql_injection(payload_data: AttackPayload):
    """模擬 SQL 注入攻擊並檢查 Laravel API 的防禦"""
    url = f"{LARAVEL_API_BASE_URL}{payload_data.target_endpoint}"
    params = {"name": payload_data.payload}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, params=params, timeout=10)
            
            # 檢查是否返回了預期的狀態碼
            if response.status_code != payload_data.expected_status:
                return {"status": "failed", "message": f"非預期狀態碼: {response.status_code}. 響應: {response.text}", "response": response.text}
            
            # 進一步檢查響應內容是否表明存在 SQL 注入漏洞
            response_text_lower = response.text.lower()
            if "sqlstate" in response_text_lower or \
               "syntax error" in response_text_lower or \
               "mysql_fetch_array" in response_text_lower or \
               ("warning" in response_text_lower and ("odbc" in response_text_lower or "mysqli" in response_text_lower)):
                return {"status": "failed", "message": f"SQL 注入漏洞被偵測到！響應包含敏感錯誤信息: {response.text}", "response": response.text}
            
            # 如果狀態碼符合預期且沒有明顯錯誤信息，則認為防禦成功
            return {"status": "success", "message": "成功防禦 SQL 注入", "response": response.text}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"請求 Laravel API 失敗: {e}")

@router.post("/simulate_xss")
async def simulate_xss(payload_data: AttackPayload):
    """模擬 XSS 攻擊並檢查 Laravel API 的防禦"""
    url = f"{LARAVEL_API_BASE_URL}{payload_data.target_endpoint}"
    data = {"content": payload_data.payload}

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, headers=payload_data.headers, timeout=10)
            
            if response.status_code != payload_data.expected_status:
                return {"status": "failed", "message": f"非預期狀態碼: {response.status_code}. 響應: {response.text}", "response": response.text}
            
            # 檢查原始 XSS payload 是否未被轉義就出現在響應中
            # 注意: 如果 payload_data.payload 是 '<script>alert("XSS")</script>'
            # 則預期 response.text 不應該直接包含 '<script>'
            if '<script>' in payload_data.payload and payload_data.payload in response.text:
                return {"status": "failed", "message": f"XSS 防禦失敗！原始 payload 未被轉義。響應: {response.text}", "response": response.text}
            
            # 檢查是否被正確轉義
            if '&lt;script&gt;' in response.text and '&lt;script&gt;alert(&quot;XSSed!&quot;)&lt;/script&gt;' in response.text:
                return {"status": "success", "message": "成功防禦 XSS (內容已轉義)", "response": response.text}
            
            return {"status": "success", "message": "成功防禦 XSS (未檢測到原始 payload 或已正確處理)", "response": response.text}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"請求 Laravel API 失敗: {e}")

@router.post("/simulate_broken_auth")
async def simulate_broken_auth(payload_data: AttackPayload):
    """模擬無效的認證嘗試（例如使用無效 JWT Token）"""
    url = f"{LARAVEL_API_BASE_URL}{payload_data.target_endpoint}"
    headers = {"Authorization": f"Bearer {payload_data.payload}"} # payload 為無效 token

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout=10)
            
            if response.status_code == payload_data.expected_status: # 預期 401 Unauthorized
                return {"status": "success", "message": f"成功處理弱認證：收到預期狀態碼 {response.status_code}", "response": response.text}
            
            return {"status": "failed", "message": f"未達到預期狀態碼: {response.status_code}. 響應: {response.text}", "response": response.text}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"請求 Laravel API 失敗: {e}")

@router.post("/simulate_login")
async def simulate_login(payload_data: AttackPayload):
    """模擬用戶登入以獲取認證 token"""
    url = f"{LARAVEL_API_BASE_URL}{payload_data.target_endpoint}"
    # payload 預期為 JSON 字串，需要解析
    try:
        data = json.loads(payload_data.payload)
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Payload 不是有效的 JSON 格式")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, json=data, timeout=10)
            
            if response.status_code == payload_data.expected_status:
                try:
                    response_json = response.json()
                    if "token" in response_json:
                        return {"status": "success", "message": "登入成功，已獲取 Token", "response": response_json}
                    else:
                        return {"status": "failed", "message": "登入成功但未在響應中找到 Token", "response": response_json}
                except json.JSONDecodeError:
                     return {"status": "failed", "message": f"登入成功但響應不是有效 JSON: {response.text}", "response": response.text}
            
            return {"status": "failed", "message": f"登入失敗或非預期狀態碼: {response.status_code}. 響應: {response.text}", "response": response.text}
        except httpx.RequestError as e:
            raise HTTPException(status_code=500, detail=f"請求 Laravel API 失敗: {e}")

