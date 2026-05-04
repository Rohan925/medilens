from pathlib import Path
import logging
from logging.config import dictConfig

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Load backend_v2/.env before importing modules that may instantiate clients.
load_dotenv(Path(__file__).resolve().parents[1] / ".env")

dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "standard": {
                "format": "%(asctime)s | %(levelname)-7s | %(name)-15s | %(message)s",
                "datefmt": "%H:%M:%S",
            }
        },
        "handlers": {
            "default": {
                "class": "logging.StreamHandler",
                "formatter": "standard",
            }
        },
        "root": {"level": "INFO", "handlers": ["default"]},
        "loggers": {
            "httpx": {"level": "WARNING", "handlers": ["default"], "propagate": False},
            "openai": {"level": "WARNING", "handlers": ["default"], "propagate": False},
            "uvicorn.access": {"level": "INFO", "handlers": ["default"], "propagate": False},
        },
    }
)

from app.api.routes.search import router as search_router
from app.api.routes.chat import router as chat_router
from app.api.routes.ocr import router as ocr_router


app = FastAPI(title="MediLens Backend V2")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(search_router)
app.include_router(chat_router)
app.include_router(ocr_router)
