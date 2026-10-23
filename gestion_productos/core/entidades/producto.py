from datetime import datetime
from typing import Optional
from gestion_productos.core.excepciones import ErrorValidacionProducto


class Producto:
    """
    Entidad de dominio que representa un Producto en el negocio.
    Contiene sus atributos y la aplicación estricta de sus reglas de validación.
    Completamente desacoplada de la base de datos (SQLAlchemy) y la web (Flask).
    """

    def __init__(
        self,
        codigo: str,
        nombre: str,
        precio: float,
        cantidad: int,
        descripcion: Optional[str] = "",
        id: Optional[int] = None,
        fecha_registro: Optional[datetime] = None,
    ):
        self.id = id
        self.codigo = codigo
        self.nombre = nombre
        self.descripcion = descripcion or ""
        self.precio = precio
        self.cantidad = cantidad
        self.fecha_registro = fecha_registro or datetime.utcnow()

        # Validación inmediata de invariantes del negocio
        self.validar()

    def validar(self) -> None:
        """
        Valida las reglas de negocio del Producto:
        - El código es obligatorio y no puede estar vacío.
        - El nombre es obligatorio y no puede estar vacío.
        - El precio no puede ser negativo.
        - La cantidad debe ser un número entero mayor o igual a cero.
        """
        if self.codigo is None or not str(self.codigo).strip():
            raise ErrorValidacionProducto("El código del producto es obligatorio.")

        if self.nombre is None or not str(self.nombre).strip():
            raise ErrorValidacionProducto("El nombre del producto es obligatorio.")

        # Normalización de strings limpios
        self.codigo = str(self.codigo).strip()
        self.nombre = str(self.nombre).strip()
        if self.descripcion is not None:
            self.descripcion = str(self.descripcion).strip()

        # Validación de precio
        try:
            self.precio = float(self.precio)
        except (ValueError, TypeError):
            raise ErrorValidacionProducto("El precio debe ser un valor numérico válido.")

        if self.precio < 0:
            raise ErrorValidacionProducto("El precio no puede ser negativo.")

        # Validación de cantidad
        if not isinstance(self.cantidad, int) and not (
            isinstance(self.cantidad, (float, str)) and str(self.cantidad).isdigit()
        ):
            raise ErrorValidacionProducto("La cantidad debe ser un número entero.")

        try:
            self.cantidad = int(self.cantidad)
        except (ValueError, TypeError):
            raise ErrorValidacionProducto("La cantidad debe ser un número entero.")

        if self.cantidad < 0:
            raise ErrorValidacionProducto("La cantidad debe ser mayor o igual a cero.")

    def actualizar(
        self,
        nombre: str,
        descripcion: Optional[str],
        precio: float,
        cantidad: int,
    ) -> None:
        """
        Actualiza los datos modificables del producto y vuelve a validar las reglas.
        El código del producto no se modifica para preservar su identidad única.
        """
        self.nombre = nombre
        self.descripcion = descripcion or ""
        self.precio = precio
        self.cantidad = cantidad
        self.validar()

    def __repr__(self) -> str:
        return (
            f"<Producto id={self.id} codigo='{self.codigo}' "
            f"nombre='{self.nombre}' precio={self.precio} cantidad={self.cantidad}>"
        )
