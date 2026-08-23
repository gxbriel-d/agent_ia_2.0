import psycopg2
from psycopg2.extras import RealDictCursor
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

def get_db_connection():
    if not settings.NEON_DATABASE_URL:
        raise ValueError("NEON_DATABASE_URL não configurada no arquivo .env")
    return psycopg2.connect(settings.NEON_DATABASE_URL, cursor_factory=RealDictCursor)

def execute_query(query: str, params: tuple = None, fetch_all: bool = True):
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            if fetch_all:
                result = cur.fetchall()
            else:
                result = cur.fetchone()
            return result
    except Exception as e:
        logger.error(f"Erro ao executar query no Neon: {e}")
        raise e
    finally:
        if conn:
            conn.close()

def execute_write(query: str, params: tuple = None) -> bool:
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute(query, params or ())
            conn.commit()
            return True
    except Exception as e:
        logger.error(f"Erro ao executar escrita no Neon: {e}")
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()
