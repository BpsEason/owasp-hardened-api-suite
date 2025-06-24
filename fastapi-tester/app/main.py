from fastapi import FastAPI
from app.api import attack_simulator

app = FastAPI(
    title="FastAPI Security Tester",
    description="用於測試 Laravel API 安全性的 FastAPI 應用",
    version="1.0.0"
)

app.include_router(attack_simulator.router, prefix="/attack", tags=["attack-simulation"])

@app.get("/")
async def root():
    return {"message": "FastAPI Security Tester is running!"}
