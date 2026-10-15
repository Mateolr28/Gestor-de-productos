from typing import List, Optional
from sqlalchemy.orm import Session
from gestion_productos.dominio.producto import Producto
from gestion_productos.dominio.interfaces.repositorio_productos import RepositorioProductos
from gestion_productos.infraestructura.modelo_producto import ProductoORM
from gestion_productos.infraestructura.mapper_producto import MapperProducto


class RepositorioProductosSQLAlchemy(RepositorioProductos):
    """
    Implementación concreta de RepositorioProductos utilizando SQLAlchemy y SQLite.
    Cumple con el contrato definido en la interfaz de la capa de dominio.
    Utiliza MapperProducto para traducir entre el modelo ORM y la entidad del dominio.
    """

    def __init__(self, session: Session):
        self.session = session

    def guardar(self, producto: Producto) -> Producto:
        """
        Persiste un nuevo producto en la base de datos a través de SQLAlchemy.
        """
        orm = MapperProducto.a_orm(producto)
        self.session.add(orm)
        self.session.commit()
        self.session.refresh(orm)
        return MapperProducto.a_entidad(orm)

    def buscar_por_id(self, producto_id: int) -> Optional[Producto]:
        """
        Busca un producto por su clave primaria en SQLite.
        """
        orm = self.session.query(ProductoORM).filter(ProductoORM.id == producto_id).first()
        if orm is None:
            return None
        return MapperProducto.a_entidad(orm)

    def buscar_por_codigo(self, codigo: str) -> Optional[Producto]:
        """
        Busca un producto por su código único de negocio.
        """
        if not codigo:
            return None
        orm = (
            self.session.query(ProductoORM)
            .filter(ProductoORM.codigo == str(codigo).strip())
            .first()
        )
        if orm is None:
            return None
        return MapperProducto.a_entidad(orm)

    def listar_todos(self) -> List[Producto]:
        """
        Retorna todos los productos ordenados cronológicamente de forma descendente.
        """
        registros = (
            self.session.query(ProductoORM)
            .order_by(ProductoORM.fecha_registro.desc(), ProductoORM.id.desc())
            .all()
        )
        return [MapperProducto.a_entidad(r) for r in registros]

    def actualizar(self, producto: Producto) -> Producto:
        """
        Actualiza el registro en la base de datos con los datos de la entidad de dominio.
        """
        orm = self.session.query(ProductoORM).filter(ProductoORM.id == producto.id).first()
        if orm is None:
            return None

        MapperProducto.actualizar_orm(orm, producto)
        self.session.commit()
        self.session.refresh(orm)
        return MapperProducto.a_entidad(orm)

    def eliminar(self, producto_id: int) -> bool:
        """
        Elimina el registro asociado al ID en la base de datos.
        """
        orm = self.session.query(ProductoORM).filter(ProductoORM.id == producto_id).first()
        if orm is None:
            return False

        self.session.delete(orm)
        self.session.commit()
        return True
