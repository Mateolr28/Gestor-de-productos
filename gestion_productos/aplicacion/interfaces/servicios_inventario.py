from abc import ABC, abstractmethod


class ServiciosInventario(ABC):
    """
    Puerto de entrada para los casos de uso adicionales del inventario.

    La interfaz pertenece a la aplicación y no conoce Flask, SQLAlchemy ni
    ningún detalle de infraestructura.
    """

    @abstractmethod
    def producto_tiene_stock(self, cantidad: int) -> bool:
        """Indica si una cantidad representa unidades disponibles."""
        pass

    @abstractmethod
    def validar_stock_producto(self, producto_id: int) -> None:
        """
        Valida que el producto exista y tenga unidades disponibles.

        No retorna un valor. Si la validación falla, lanza una excepción de
        dominio para que el adaptador de entrada decida cómo comunicarlo.
        """
        pass

    @abstractmethod
    def generar_resumen_inventario(self) -> str:
        """Genera un resumen textual del inventario actual."""
        pass
