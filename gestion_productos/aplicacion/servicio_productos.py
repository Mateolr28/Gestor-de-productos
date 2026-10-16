from typing import List, Optional
from gestion_productos.dominio.producto import Producto
from gestion_productos.dominio.interfaces.repositorio_productos import RepositorioProductos
from gestion_productos.dominio.excepciones import (
    ProductoNoEncontradoError,
    CodigoProductoDuplicadoError,
    ProductoSinStockError,
)
from gestion_productos.aplicacion.interfaces.servicios_inventario import (
    ServiciosInventario,
)


class ServicioProductos(ServiciosInventario):
    """
    Capa de aplicación / Casos de uso.
    Coordina la ejecución de las operaciones de negocio sobre los productos.
    Recibe la abstracción RepositorioProductos mediante inyección de dependencias.
    No depende de ningún framework web (Flask) ni motor ORM (SQLAlchemy).
    """

    def __init__(self, repositorio: RepositorioProductos):
        if not isinstance(repositorio, RepositorioProductos):
            raise TypeError("El repositorio debe implementar la interfaz RepositorioProductos.")
        self.repositorio = repositorio

    def registrar_producto(
        self,
        codigo: str,
        nombre: str,
        precio: float,
        cantidad: int,
        descripcion: str = "",
    ) -> Producto:
        """
        Caso de uso: Registrar un nuevo producto.
        Valida que el código no exista previamente en el repositorio,
        construye la entidad de dominio y delega su persistencia.
        """
        codigo_limpio = str(codigo).strip() if codigo is not None else ""

        # Verificar unicidad del código
        existente = self.repositorio.buscar_por_codigo(codigo_limpio)
        if existente is not None:
            raise CodigoProductoDuplicadoError(
                f"Ya existe un producto registrado con el código '{codigo_limpio}'."
            )

        # La creación de Producto dispara automáticamente las validaciones del dominio
        nuevo_producto = Producto(
            codigo=codigo_limpio,
            nombre=nombre,
            precio=precio,
            cantidad=cantidad,
            descripcion=descripcion,
        )

        return self.repositorio.guardar(nuevo_producto)

    def consultar_productos(self) -> List[Producto]:
        """
        Caso de uso: Consultar todos los productos registrados.
        """
        return self.repositorio.listar_todos()

    def buscar_productos(self, termino: Optional[str]) -> List[Producto]:
        """
        Caso de uso: Buscar productos por nombre o código.
        Si el término está vacío, retorna la lista completa.
        """
        todos = self.repositorio.listar_todos()
        if not termino or not str(termino).strip():
            return todos

        t = str(termino).strip().lower()
        return [
            p for p in todos
            if t in p.nombre.lower() or t in p.codigo.lower()
        ]

    def obtener_producto_por_id(self, producto_id: int) -> Producto:
        """
        Caso de uso: Obtener un producto específico por su ID numérico.
        Lanza ProductoNoEncontradoError si no existe.
        """
        producto = self.repositorio.buscar_por_id(producto_id)
        if producto is None:
            raise ProductoNoEncontradoError(
                f"El producto con ID {producto_id} no existe en el sistema."
            )
        return producto

    def obtener_total_productos(self) -> int:
        """
        Caso de uso: Obtener la cantidad total de productos registrados.
        """
        return len(self.repositorio.listar_todos())

    def actualizar_producto(
        self,
        producto_id: int,
        nombre: str,
        descripcion: str,
        precio: float,
        cantidad: int,
    ) -> Producto:
        """
        Caso de uso: Actualizar los datos de un producto existente.
        Valida la existencia, actualiza la entidad con reglas de negocio y persiste.
        """
        producto = self.obtener_producto_por_id(producto_id)

        # Actualiza el estado de la entidad (vuelve a validar reglas de negocio)
        producto.actualizar(
            nombre=nombre,
            descripcion=descripcion,
            precio=precio,
            cantidad=cantidad,
        )

        return self.repositorio.actualizar(producto)

    def eliminar_producto(self, producto_id: int) -> bool:
        """
        Caso de uso: Eliminar un producto por su ID.
        Verifica que el producto exista antes de solicitar su eliminación.
        """
        # Asegurar que el producto existe
        self.obtener_producto_por_id(producto_id)
        return self.repositorio.eliminar(producto_id)

    def producto_tiene_stock(self, producto_id: int) -> bool:
        """
        Caso de uso: comprobar si un producto tiene unidades disponibles.
        """
        producto = self.obtener_producto_por_id(producto_id)
        return producto.cantidad > 0

    def validar_stock_producto(self, producto_id: int) -> None:
        """
        Caso de uso: validar que un producto pueda ser utilizado o vendido.

        El contrato no retorna datos; una validación correcta termina
        normalmente y una inválida comunica el motivo mediante una excepción.
        """
        producto = self.obtener_producto_por_id(producto_id)
        if producto.cantidad <= 0:
            raise ProductoSinStockError(
                f"El producto con ID {producto_id} no tiene unidades disponibles."
            )

    def generar_resumen_inventario(self) -> str:
        """
        Caso de uso: generar una salida textual con el estado del inventario.
        """
        productos = self.repositorio.listar_todos()
        unidades = sum(producto.cantidad for producto in productos)
        valor = sum(producto.precio * producto.cantidad for producto in productos)
        return (
            f"Productos registrados: {len(productos)} | "
            f"Unidades en inventario: {unidades} | "
            f"Valor del inventario: ${valor:,.2f}"
        )
