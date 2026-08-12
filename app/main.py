import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.telegram_webhook import router as telegram_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("app.main")

app = FastAPI(
    title="Agente de Orçamentos de Vidraçaria & Esquadrias (Protocolo V.L.A.E.G.)",
    version="2.0.0",
    description="Sistema de Orçamentos de Vidraçaria via Telegram + LangGraph + Quote Service + Neon + Redis"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(telegram_router)

@app.get("/health")
def health_check():
    """
    Endpoint de verificação de saúde da aplicação.
    """
    return {
        "status": "healthy",
        "app_name": "Agente Orçamentos Vidraçaria",
        "model": settings.OPENAI_MODEL,
        "debounce_seconds": settings.DEBOUNCE_SECONDS,
        "timezone": settings.TIMEZONE
    }

@app.on_event("startup")
def startup_event():
    logger.info(f"=== Inicializando Agente de Orçamentos (Porta: {settings.APP_PORT}) ===")
    logger.info(f"LangSmith Tracing: {settings.LANGCHAIN_TRACING_V2}")
    logger.info(f"Fuso Horário Oficial: {settings.TIMEZONE}")
