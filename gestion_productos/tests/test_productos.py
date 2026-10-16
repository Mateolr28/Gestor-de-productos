"""
Conjunto completo de pruebas automatizadas con pytest para el Gestor de Productos.
Comprueba:
- Validación y comportamiento de la entidad de Dominio.
- Casos de uso de ServicioProductos utilizando un Repositorio en Memoria (aislamiento puro).
- Persistencia real en base de datos SQLite aislada mediante RepositorioProductosSQLAlchemy y Mapper.
- Capa de presentación Flask mediante cliente de pruebas web.
"""

import pytest
from datetime import datetime
from typing import List, Optional

from gestion_productos.dominio.producto import Producto
from gestion_productos.dominio.interfaces.repositorio_productos import RepositorioProductos
from gestion_productos.dominio.excepciones import (
    ErrorValidacionProducto,
    ProductoNoEncontradoError,
    CodigoProductoDuplicadoError,
    ProductoSinStockError,
)
from gestion_productos.aplicacion.servicio_productos import ServicioProductos
from gestion_productos.infraestructura.modelo_producto import Base, ProductoORM
from gestion_productos.infraestructura.mapper_producto import MapperProducto
from gestion_productos.infraestructura.repositorio_productos_sqlalchemy import (
    RepositorioProductosSQLAlchemy,
)
from gestion_productos.infraestructura.base_datos import (
    obtener_motor,
    crear_fabrica_sesiones,
    inicializar_base_datos,
)
from gestion_productos.presentacion.rutas import crear_app, parsear_precio, formato_pesos


# ==============================================================================
# 1. IMPLEMENTACIÓN DE PRUEBA (MOCK/STUB) DEL REPOSITORIO
# Demuestra el principio de inversión de dependencias: el servicio funciona
# perfectamente con cualquier implementación que respete la interfaz abstracta.
# ==============================================================================

class RepositorioProductosEnMemoria(RepositorioProductos):
    """Repositorio en memoria utilizado exclusivamente para probar el servicio en aislamiento."""

    def __init__(self):
        self._items = {}
        self._secuencia = 1

    def guardar(self, producto: Producto) -> Producto:
        producto.id = self._secuencia
        self._secuencia += 1
        self._items[producto.id] = producto
        return producto

    def buscar_por_id(self, producto_id: int) -> Optional[Producto]:
        return self._items.get(producto_id)

    def buscar_por_codigo(self, codigo: str) -> Optional[Producto]:
        codigo_norm = str(codigo).strip().lower()
        for prod in self._items.values():
            if prod.codigo.lower() == codigo_norm:
                return prod
        return None

    def listar_todos(self) -> List[Producto]:
        return list(self._items.values())

    def actualizar(self, producto: Producto) -> Producto:
        self._items[producto.id] = producto
        return producto

    def eliminar(self, producto_id: int) -> bool:
        if producto_id in self._items:
            del self._items[producto_id]
            return True
        return False


# ==============================================================================
# 2. FIXTURES DE PYTEST
# ==============================================================================

@pytest.fixture
def repo_memoria():
    return RepositorioProductosEnMemoria()


@pytest.fixture
def servicio_con_memoria(repo_memoria):
    return ServicioProductos(repositorio=repo_memoria)


@pytest.fixture
def db_sqlite_aislada():
    """Crea una base de datos SQLite en memoria completamente aislada para cada test."""
    engine = obtener_motor("sqlite:///:memory:")
    inicializar_base_datos(engine)
    session_factory = crear_fabrica_sesiones(engine)
    session = session_factory()
    repo = RepositorioProductosSQLAlchemy(session)
    servicio = ServicioProductos(repo)
    yield servicio, repo, session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def app_cliente_web(db_sqlite_aislada):
    """Cliente de pruebas para la interfaz web Flask."""
    servicio, _, _ = db_sqlite_aislada
    app = crear_app(servicio_productos=servicio)
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as client:
        yield client, servicio


# ==============================================================================
# 3. PRUEBAS DE LA ENTIDAD DE DOMINIO
# ==============================================================================

def test_crear_producto_dominio_valido():
    prod = Producto(
        codigo="PR-01",
        nombre="Teclado",
        precio=25.50,
        cantidad=10,
        descripcion="Teclado de oficina",
    )
    assert prod.codigo == "PR-01"
    assert prod.nombre == "Teclado"
    assert prod.precio == 25.50
    assert prod.cantidad == 10
    assert isinstance(prod.fecha_registro, datetime)


def test_validacion_codigo_vacio_falla():
    with pytest.raises(ErrorValidacionProducto, match="código .* obligatorio"):
        Producto(codigo="", nombre="Mouse", precio=10.0, cantidad=5)

    with pytest.raises(ErrorValidacionProducto):
        Producto(codigo="   ", nombre="Mouse", precio=10.0, cantidad=5)


def test_validacion_nombre_vacio_falla():
    with pytest.raises(ErrorValidacionProducto, match="nombre .* obligatorio"):
        Producto(codigo="PR-02", nombre="", precio=10.0, cantidad=5)


def test_validacion_precio_negativo_falla():
    with pytest.raises(ErrorValidacionProducto, match="precio no puede ser negativo"):
        Producto(codigo="PR-03", nombre="Mouse", precio=-5.0, cantidad=5)


def test_validacion_cantidad_negativa_o_invalida_falla():
    with pytest.raises(ErrorValidacionProducto, match="mayor o igual a cero"):
        Producto(codigo="PR-04", nombre="Mouse", precio=10.0, cantidad=-1)

    with pytest.raises(ErrorValidacionProducto, match="número entero"):
        Producto(codigo="PR-05", nombre="Mouse", precio=10.0, cantidad=3.5)


def test_actualizar_producto_dominio():
    prod = Producto(codigo="PR-10", nombre="Original", precio=10.0, cantidad=2)
    prod.actualizar(nombre="Modificado", descripcion="Nueva desc", precio=15.0, cantidad=5)
    assert prod.nombre == "Modificado"
    assert prod.precio == 15.0
    assert prod.cantidad == 5


def test_formato_y_parseo_de_precios_en_pesos():
    assert parsear_precio("1.000.000") == 1_000_000
    assert parsear_precio("1.000.000,50") == 1_000_000.50
    assert formato_pesos(1_000_000) == "1.000.000"
    assert formato_pesos(1_000_000.50) == "1.000.000,50"


def test_web_registro_acepta_precio_en_pesos(app_cliente_web):
    client, servicio = app_cliente_web
    response = client.post(
        "/productos/nuevo",
        data={
            "codigo": "PESO-001",
            "nombre": "Producto costoso",
            "precio": "1.000.000",
            "cantidad": "1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "$1.000.000" in response.data.decode("utf-8")
    assert servicio.consultar_productos()[0].precio == 1_000_000


def test_web_registro_acepta_precio_formateado_de_seis_digitos(app_cliente_web):
    client, servicio = app_cliente_web
    response = client.post(
        "/productos/nuevo",
        data={
            "codigo": "PESO-100",
            "nombre": "Producto de cien mil",
            "precio": "100.000",
            "cantidad": "1",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "registrado exitosamente" in response.data.decode("utf-8")
    assert servicio.consultar_productos()[0].precio == 100_000


# ==============================================================================
# 4. PRUEBAS DEL SERVICIO (CASOS DE USO CON REPOSITORIO DE PRUEBA)
# ==============================================================================

def test_servicio_registrar_producto_exitoso(servicio_con_memoria):
    prod = servicio_con_memoria.registrar_producto(
        codigo="A-01",
        nombre="Monitor",
        precio=150.0,
        cantidad=4,
        descripcion="24 pulgadas",
    )
    assert prod.id is not None
    assert prod.codigo == "A-01"
    assert servicio_con_memoria.obtener_total_productos() == 1


def test_servicio_rechazo_codigo_duplicado(servicio_con_memoria):
    servicio_con_memoria.registrar_producto(
        codigo="DUP-01", nombre="Original", precio=50.0, cantidad=2
    )

    with pytest.raises(CodigoProductoDuplicadoError, match="Ya existe un producto"):
        servicio_con_memoria.registrar_producto(
            codigo="DUP-01", nombre="Duplicado", precio=80.0, cantidad=1
        )


def test_servicio_consultar_y_buscar_productos(servicio_con_memoria):
    servicio_con_memoria.registrar_producto(codigo="LAP-01", nombre="Laptop Lenovo", precio=800.0, cantidad=3)
    servicio_con_memoria.registrar_producto(codigo="LAP-02", nombre="Laptop Asus", precio=950.0, cantidad=5)
    servicio_con_memoria.registrar_producto(codigo="AUD-03", nombre="Auriculares Sony", precio=60.0, cantidad=10)

    # Consulta total
    assert len(servicio_con_memoria.consultar_productos()) == 3

    # Búsqueda por nombre
    res_asus = servicio_con_memoria.buscar_productos("Asus")
    assert len(res_asus) == 1
    assert res_asus[0].codigo == "LAP-02"

    # Búsqueda por código
    res_cod = servicio_con_memoria.buscar_productos("AUD")
    assert len(res_cod) == 1

    # Búsqueda término vacío retorna todos
    assert len(servicio_con_memoria.buscar_productos("")) == 3


def test_servicio_actualizar_producto(servicio_con_memoria):
    prod = servicio_con_memoria.registrar_producto(
        codigo="ACT-01", nombre="Mouse", precio=12.0, cantidad=10
    )

    actualizado = servicio_con_memoria.actualizar_producto(
        producto_id=prod.id,
        nombre="Mouse Gamer",
        descripcion="Con luces RGB",
        precio=22.50,
        cantidad=15,
    )
    assert actualizado.nombre == "Mouse Gamer"
    assert actualizado.precio == 22.50
    assert actualizado.cantidad == 15


def test_servicio_eliminar_producto(servicio_con_memoria):
    prod = servicio_con_memoria.registrar_producto(
        codigo="DEL-01", nombre="Parlante", precio=30.0, cantidad=8
    )
    assert servicio_con_memoria.obtener_total_productos() == 1

    exito = servicio_con_memoria.eliminar_producto(prod.id)
    assert exito is True
    assert servicio_con_memoria.obtener_total_productos() == 0


def test_servicio_producto_tiene_stock_retorna_booleano(servicio_con_memoria):
    assert servicio_con_memoria.producto_tiene_stock(2) is True
    assert servicio_con_memoria.producto_tiene_stock(0) is False
    assert servicio_con_memoria.producto_tiene_stock(-1) is False


def test_servicio_validar_stock_no_retorna_y_falla_sin_stock(servicio_con_memoria):
    producto_disponible = servicio_con_memoria.registrar_producto(
        codigo="STOCK-02",
        nombre="Producto disponible",
        precio=10.0,
        cantidad=1,
    )
    resultado = servicio_con_memoria.validar_stock_producto(producto_disponible.id)
    assert resultado is None

    producto_agotado = servicio_con_memoria.registrar_producto(
        codigo="STOCK-03",
        nombre="Producto agotado",
        precio=10.0,
        cantidad=0,
    )

    with pytest.raises(ProductoSinStockError):
        servicio_con_memoria.validar_stock_producto(producto_agotado.id)


def test_servicio_generar_resumen_inventario_sin_parametros(servicio_con_memoria):
    servicio_con_memoria.registrar_producto(
        codigo="RES-01",
        nombre="Producto uno",
        precio=100.0,
        cantidad=2,
    )
    servicio_con_memoria.registrar_producto(
        codigo="RES-02",
        nombre="Producto dos",
        precio=50.0,
        cantidad=1,
    )

    assert servicio_con_memoria.generar_resumen_inventario() == (
        "Productos registrados: 2 | Unidades en inventario: 3 | "
        "Valor del inventario: $250.00"
    )


def test_servicio_producto_inexistente_lanza_error(servicio_con_memoria):
    with pytest.raises(ProductoNoEncontradoError):
        servicio_con_memoria.obtener_producto_por_id(9999)

    with pytest.raises(ProductoNoEncontradoError):
        servicio_con_memoria.actualizar_producto(
            producto_id=9999,
            nombre="Cualquiera",
            descripcion="",
            precio=10.0,
            cantidad=1,
        )

    with pytest.raises(ProductoNoEncontradoError):
        servicio_con_memoria.eliminar_producto(9999)


# ==============================================================================
# 5. PRUEBAS DE INFRAESTRUCTURA Y PERSISTENCIA REAL (SQLITE + SQLALCHEMY + MAPPER)
# ==============================================================================

def test_mapper_bidireccional():
    dominio = Producto(
        id=7,
        codigo="MAP-01",
        nombre="Webcam HD",
        precio=45.0,
        cantidad=8,
        descripcion="1080p 60fps",
    )
    # Dominio -> ORM
    orm = MapperProducto.a_orm(dominio)
    assert isinstance(orm, ProductoORM)
    assert orm.codigo == "MAP-01"
    assert orm.precio == 45.0

    # ORM -> Dominio
    convertido = MapperProducto.a_entidad(orm)
    assert isinstance(convertido, Producto)
    assert convertido.codigo == "MAP-01"
    assert convertido.nombre == "Webcam HD"


def test_persistencia_sqlite_repositorio_sqlalchemy(db_sqlite_aislada):
    servicio, repo, session = db_sqlite_aislada

    # Guardar entidad en SQLite
    prod = Producto(
        codigo="SQL-01",
        nombre="Disco SSD 1TB",
        precio=85.0,
        cantidad=20,
        descripcion="NVMe PCIe 4.0",
    )
    guardado = repo.guardar(prod)
    assert guardado.id is not None

    # Recuperar directamente desde SQLite
    recuperado = repo.buscar_por_id(guardado.id)
    assert recuperado is not None
    assert recuperado.codigo == "SQL-01"
    assert recuperado.nombre == "Disco SSD 1TB"
    assert recuperado.precio == 85.0

    # Buscar por código
    por_cod = repo.buscar_por_codigo("SQL-01")
    assert por_cod is not None
    assert por_cod.id == guardado.id

    # Actualizar en SQLite
    guardado.actualizar(
        nombre="Disco SSD 2TB",
        descripcion="Actualizado",
        precio=140.0,
        cantidad=10,
    )
    repo.actualizar(guardado)

    recuperado_act = repo.buscar_por_id(guardado.id)
    assert recuperado_act.nombre == "Disco SSD 2TB"
    assert recuperado_act.precio == 140.0

    # Eliminar en SQLite
    eliminado = repo.eliminar(guardado.id)
    assert eliminado is True
    assert repo.buscar_por_id(guardado.id) is None


# ==============================================================================
# 6. PRUEBAS DE LA CAPA DE PRESENTACIÓN WEB (FLASK ROUTES)
# ==============================================================================

def test_web_index_y_lista_vacia(app_cliente_web):
    client, _ = app_cliente_web
    response = client.get("/")
    assert response.status_code == 200
    assert b"Gestor de Productos" in response.data
    assert "Aún no hay productos registrados" in response.data.decode("utf-8")


def test_web_inventario_muestra_resumen(app_cliente_web):
    client, servicio = app_cliente_web
    servicio.registrar_producto(
        codigo="INV-01",
        nombre="Producto inventario",
        precio=25.0,
        cantidad=4,
    )

    response = client.get("/inventario")

    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Resumen de Inventario" in html
    assert "Productos registrados: 1" in html
    assert "Unidades en inventario: 4" in html
    assert "$100.00" in html


def test_web_formulario_nuevo_se_muestra_sin_producto(app_cliente_web):
    client, _ = app_cliente_web
    response = client.get("/productos/nuevo")
    assert response.status_code == 200
    assert "Registrar Nuevo Producto" in response.data.decode("utf-8")


def test_web_registro_producto_exitoso(app_cliente_web):
    client, servicio = app_cliente_web

    # Enviar formulario POST
    response = client.post(
        "/productos/nuevo",
        data={
            "codigo": "WEB-100",
            "nombre": "Micrófono USB",
            "descripcion": "Condensador cardioide",
            "precio": "49.99",
            "cantidad": "15",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "registrado exitosamente" in html
    assert "WEB-100" in html
    assert "Micrófono USB" in html
    assert servicio.obtener_total_productos() == 1


def test_web_registro_rechaza_codigo_duplicado(app_cliente_web):
    client, servicio = app_cliente_web
    servicio.registrar_producto(codigo="DUP-WEB", nombre="Item 1", precio=10.0, cantidad=1)

    response = client.post(
        "/productos/nuevo",
        data={
            "codigo": "DUP-WEB",
            "nombre": "Item 2",
            "precio": "20.0",
            "cantidad": "2",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Ya existe un producto registrado con el código" in html


def test_web_registro_rechaza_precio_negativo(app_cliente_web):
    client, _ = app_cliente_web
    response = client.post(
        "/productos/nuevo",
        data={
            "codigo": "NEG-01",
            "nombre": "Item Negativo",
            "precio": "-15.0",
            "cantidad": "5",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "precio no puede ser negativo" in html


def test_web_editar_producto(app_cliente_web):
    client, servicio = app_cliente_web
    prod = servicio.registrar_producto(
        codigo="EDIT-01", nombre="Mouse Viejo", precio=10.0, cantidad=5
    )

    # Cargar formulario GET de edición
    res_get = client.get(f"/productos/{prod.id}/editar")
    assert res_get.status_code == 200
    assert "Modificar Producto" in res_get.data.decode("utf-8")

    # Enviar actualización POST
    res_post = client.post(
        f"/productos/{prod.id}/editar",
        data={
            "nombre": "Mouse Nuevo",
            "descripcion": "Bluetooth 5.0",
            "precio": "25.0",
            "cantidad": "8",
        },
        follow_redirects=True,
    )
    assert res_post.status_code == 200
    html = res_post.data.decode("utf-8")
    assert "actualizado correctamente" in html
    assert "Mouse Nuevo" in html


def test_web_eliminar_producto(app_cliente_web):
    client, servicio = app_cliente_web
    prod = servicio.registrar_producto(
        codigo="DEL-WEB", nombre="Producto a Borrar", precio=5.0, cantidad=1
    )

    response = client.post(
        f"/productos/{prod.id}/eliminar",
        follow_redirects=True,
    )
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "Producto eliminado exitosamente" in html
    assert servicio.obtener_total_productos() == 0


def test_web_editar_producto_inexistente_redirige(app_cliente_web):
    client, _ = app_cliente_web
    response = client.get("/productos/9999/editar", follow_redirects=True)
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "no existe en el sistema" in html
