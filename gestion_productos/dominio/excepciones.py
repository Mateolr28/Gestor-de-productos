class DominioError(Exception):
    """Excepción base para errores del dominio."""
    pass


class ErrorValidacionProducto(DominioError):
    """Lanzada cuando un producto no cumple las reglas de validación de negocio."""
    pass


class ProductoNoEncontradoError(DominioError):
    """Lanzada cuando se solicita un producto que no existe en el sistema."""
    pass


class CodigoProductoDuplicadoError(DominioError):
    """Lanzada cuando se intenta registrar un producto con un código ya existente."""


class ProductoSinStockError(DominioError):
    """Lanzada cuando un producto no tiene unidades disponibles."""
    pass
