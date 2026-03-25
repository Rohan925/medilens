from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from api.auth_routes import router as auth_router

from services.medicine_service import get_medicine_data
from api.ocr_routes import router as ocr_router
from api.chat_routes import router as chat_router
from database import engine
from models import Base

app = FastAPI()

app.include_router(auth_router)
Base.metadata.create_all(bind=engine)
app.include_router(ocr_router)
app.include_router(chat_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class SearchRequest(BaseModel):
    medicine: str


@app.post("/search")
async def search(req: SearchRequest):
    return await get_medicine_data(req.medicine)
