from fastapi import APIRouter
from app.api.v1.endpoints import smtp

api_router = APIRouter()
api_router.include_router(smtp.router)
