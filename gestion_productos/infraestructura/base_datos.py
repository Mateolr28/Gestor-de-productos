import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from gestion_productos.infraestructura.modelo_producto import Base


def obtener_motor(db_url: str = None):
    """
    Crea y retorna la conexión del motor (engine) de SQLAlchemy.
    Por defecto utiliza una base de datos local SQLite 'productos.db'.
    """
    if db_url is None:
        db_path = os.environ.get("DATABASE_PATH", "productos.db")
        # Asegurar ruta absoluta si es relativa al proyecto
        if not db_path.startswith("/") and not db_path.startswith("sqlite://"):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            db_path = os.path.join(base_dir, "productos.db")
            db_url = f"sqlite:///{db_path}"
        elif not db_url:
            db_url = f"sqlite:///{db_path}"

    return create_engine(db_url, connect_args={"check_same_thread": False})


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
