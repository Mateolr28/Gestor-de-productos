from gestion_productos.core.entidades.producto import Producto
from gestion_productos.infrastructure.persistencia.modelo_producto import ProductoORM


class MapperProducto:
    """
    Data Mapper Pattern.
    Responsable exclusivo de la traducción bidireccional entre la entidad pura
    del Dominio (Producto) y el modelo relacional de la Infraestructura (ProductoORM).
    Esto aísla por completo el modelo de dominio de cualquier detalle o esquema de base de datos.
    """

    @staticmethod
    def a_entidad(orm: ProductoORM) -> Producto:
        """
        Convierte una instancia de ProductoORM a la entidad de Dominio Producto.
        """
        if orm is None:
            return None

        return Producto(
            id=orm.id,
            codigo=orm.codigo,
            nombre=orm.nombre,
            descripcion=orm.descripcion or "",
            precio=float(orm.precio),
            cantidad=int(orm.cantidad),
            fecha_registro=orm.fecha_registro,
        )

    @staticmethod
    def a_orm(dominio: Producto) -> ProductoORM:
        """
        Convierte una entidad de Dominio Producto a un objeto ProductoORM para persistencia.
        """
        if dominio is None:
            return None

        return ProductoORM(
            id=dominio.id,
            codigo=dominio.codigo,
            nombre=dominio.nombre,
            descripcion=dominio.descripcion or "",
            precio=dominio.precio,
            cantidad=dominio.cantidad,
            fecha_registro=dominio.fecha_registro,
        )

    @staticmethod
    def actualizar_orm(orm: ProductoORM, dominio: Producto) -> None:
        """
        Sincroniza el estado del objeto ORM existente con los valores del Dominio.
        """
        orm.nombre = dominio.nombre
        orm.descripcion = dominio.descripcion or ""
        orm.precio = dominio.precio
        orm.cantidad = dominio.cantidad
