# backend/api/search_routes.py
from fastapi import APIRouter
from pydantic import BaseModel
from services.medicine_service import get_medicine_data

router = APIRouter()

class SearchRequest(BaseModel):
    medicine: str

@router.post("/search")
async def search(req: SearchRequest):
    # This now triggers the multi-agent coordinator instead of just a raw API call
    result = await get_medicine_data(req.medicine)
    return result