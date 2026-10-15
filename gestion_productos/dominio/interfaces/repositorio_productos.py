from abc import ABC, abstractmethod
from typing import List, Optional
from gestion_productos.dominio.producto import Producto


class RepositorioProductos(ABC):
    """
    Interfaz abstracta (puerto secundario) para el almacenamiento y recuperación de productos.
    Establece los contratos de persistencia sin acoplarse a ninguna tecnología específica (ORM, SQL, NoSQL).
    """

    @abstractmethod
    def guardar(self, producto: Producto) -> Producto:
        """
        Guarda un nuevo producto en el medio de persistencia.
        Retorna la entidad Producto con su ID generado asignado.
        """
        pass

    @abstractmethod
    def buscar_por_id(self, producto_id: int) -> Optional[Producto]:
        """
        Busca y retorna un producto por su identificador único numérico.
        Retorna None si no existe.
        """
        pass

    @abstractmethod
    def buscar_por_codigo(self, codigo: str) -> Optional[Producto]:
        """
        Busca y retorna un producto por su código único de negocio.
        Retorna None si no existe.
        """
        pass

    @abstractmethod
    def listar_todos(self) -> List[Producto]:
        """
        Retorna la lista completa de productos registrados.
        """
        pass

    @abstractmethod
    def actualizar(self, producto: Producto) -> Producto:
        """
        Actualiza el estado de un producto existente.
        Retorna la entidad actualizada.
        """
        pass

    @abstractmethod
    def eliminar(self, producto_id: int) -> bool:
        """
        Elimina un producto por su ID.
        Retorna True si fue eliminado exitosamente.
        """
        pass
