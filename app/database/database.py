import logging
import time

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings

# ─── Logger ───────────────────────────────────────────────────────────────────
logger = logging.getLogger(__name__)

# ─── Constantes de conexión ───────────────────────────────────────────────────
_CONNECTION_RETRIES = 3
_RETRY_DELAY_SECONDS = 2

# ─── Configuración del engine ─────────────────────────────────────────────────
#
# NullPool desactiva el pooling de conexiones.
# Esto es NECESARIO porque SQLAlchemy con pooling estándar no es compatible
# con WebSockets de larga duración: las conexiones se "prestan" al inicio
# y nunca se liberan al pool mientras el WebSocket está abierto.
# Con NullPool cada operación abre y cierra su propia conexión, lo que
# evita deadlocks y errores de "connection already closed".
#
engine = create_engine(
    settings.database_url,
    poolclass=NullPool,
    echo=settings.debug,
    connect_args={
        "sslmode": "require",
        "connect_timeout": 10,
        "keepalives": 1,
        "keepalives_idle": 30,
        "keepalives_interval": 10,
        "keepalives_count": 5,
        "options": "-c statement_timeout=30000",
    },
)

# ─── Sesión y Base ────────────────────────────────────────────────────────────
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


# ─── Dependencia FastAPI ──────────────────────────────────────────────────────
def get_db() -> Session:
    """
    Dependency para inyectar en endpoints FastAPI.
    Garantiza que la sesión se cierre al terminar el request,
    incluso si ocurre una excepción.

    Uso:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Utilidades de inicialización ─────────────────────────────────────────────
def test_connection() -> bool:
    """
    Verifica la conectividad con la base de datos.
    Reintenta hasta _CONNECTION_RETRIES veces antes de retornar False.

    Returns:
        True si la conexión fue exitosa, False en caso contrario.
    """
    for attempt in range(1, _CONNECTION_RETRIES + 1):
        try:
            with engine.connect() as connection:
                result = connection.execute(text("SELECT version();"))
                version = result.fetchone()[0]
                logger.info("Conexión exitosa a la base de datos: %s", version)
                return True
        except SQLAlchemyError as exc:
            logger.error(
                "Intento %d/%d fallido: %s",
                attempt,
                _CONNECTION_RETRIES,
                exc,
            )
            if attempt < _CONNECTION_RETRIES:
                time.sleep(_RETRY_DELAY_SECONDS)

    return False


def create_tables() -> None:
    """
    Crea todas las tablas registradas en Base.metadata.
    Solo debe usarse en entornos sin Alembic.
    En producción se recomienda gestionar migraciones con Alembic.
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tablas creadas exitosamente.")
    except SQLAlchemyError as exc:
        logger.error("Error al crear las tablas: %s", exc)
        raise