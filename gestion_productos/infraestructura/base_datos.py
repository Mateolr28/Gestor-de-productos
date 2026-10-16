import os
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker, scoped_session
from gestion_productos.infraestructura.modelo_producto import Base


def obtener_motor(db_url: str = None):
    """
    Crea y retorna la conexión del motor (engine) de SQLAlchemy.
    Por defecto utiliza una base de datos SQLite en memoria.

    StaticPool mantiene una única conexión para que la base en memoria sea
    compartida por las sesiones creadas durante la ejecución de la aplicación.
    La URL o la variable DATABASE_URL permiten sustituirla por otra base.
    """
    if db_url is None:
        db_url = os.environ.get("DATABASE_URL", "sqlite:///:memory:")

    engine_options = {}
    if db_url.startswith("sqlite"):
        engine_options["connect_args"] = {"check_same_thread": False}
        if db_url in ("sqlite:///:memory:", "sqlite://"):
            engine_options["poolclass"] = StaticPool

    return create_engine(db_url, **engine_options)


def crear_fabrica_sesiones(engine):
    """
    Crea una fábrica de sesiones con scope seguro para hilos de Flask.
    """
    session_factory = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return scoped_session(session_factory)


def inicializar_base_datos(engine):
    """
    Crea las tablas en la base de datos si todavía no existen.
    """
    Base.metadata.create_all(bind=engine)
