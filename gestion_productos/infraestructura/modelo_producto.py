from datetime import datetime
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Float, Text, DateTime

Base = declarative_base()


class ProductoORM(Base):
    """
    Modelo de persistencia para SQLAlchemy.
    Representa la tabla 'productos' en la base de datos relacional (SQLite).
    Pertenece a la capa de infraestructura y no debe ser utilizado directamente
    por la capa de dominio ni de aplicación.
    """

    __tablename__ = "productos"

    id = Column(Integer, primary_key=True, autoincrement=True)
    codigo = Column(String(50), unique=True, nullable=False, index=True)
    nombre = Column(String(150), nullable=False)
    descripcion = Column(Text, nullable=True, default="")
    precio = Column(Float, nullable=False)
    cantidad = Column(Integer, nullable=False)
    fecha_registro = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return (
            f"<ProductoORM(id={self.id}, codigo='{self.codigo}', "
            f"nombre='{self.nombre}', precio={self.precio}, cantidad={self.cantidad})>"
        )
