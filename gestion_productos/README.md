# Gestor de Productos

Sistema sencillo de gestión de productos desarrollado con **Python**, **Flask**, **SQLAlchemy** y **SQLite en memoria**, diseñado bajo una **arquitectura desacoplada** para demostrar de forma limpia y académica los principios de separación de responsabilidades, contratos de interfaz, inversión de dependencias y el patrón Data Mapper.

---

## 🏛️ Arquitectura Desacoplada

La aplicación está organizada en capas con una dirección estricta de dependencias hacia el centro (el Dominio):

```
                       ┌─────────────────────────┐
                       │       Presentación      │ (Flask, Jinja2, HTML/CSS/JS)
                       └────────────┬────────────┘
                                    │ usa
                                    ▼
                       ┌─────────────────────────┐
                       │        Aplicación       │ (ServicioProductos: Casos de uso)
                       └────────────┬────────────┘
                                    │ depende de
                                    ▼
┌─────────────────────────┐    ┌─────────────────────────┐
│     Infraestructura     ├───►│         Dominio         │ (Producto, Excepciones)
│ (SQLAlchemy, Mapper, DB)│    │       Interfaces        │ (RepositorioProductos ABC)
└─────────────────────────┘    └─────────────────────────┘
        (Implementa)                  (Define el contrato)
```

### 1. Entidades (`core/`)
- **`entidades/producto.py`**: Entidad `Producto` pura. Encapsula los atributos comerciales (`codigo`, `nombre`, `precio`, `cantidad`, `descripcion`, `fecha_registro`) y valida sus invariantes (campos obligatorios, precio $\ge 0$, cantidad entera $\ge 0$). **No importa Flask, ni SQLAlchemy, ni SQLite**.
- **`excepciones.py`**: Jerarquía de excepciones de negocio (`ErrorValidacionProducto`, `ProductoNoEncontradoError`, `CodigoProductoDuplicadoError`).

### 2. Casos de uso y puertos (`application/`)
- **`casos_de_uso/servicio_productos.py`**: Clase `ServicioProductos` que orquesta los casos de uso:
  - Registro de productos verificando unicidad de código.
  - Consulta y búsqueda por nombre o código.
  - Actualización de datos comerciales.
  - Eliminación con validación de existencia.
  - Inyección de dependencias: solo conoce la interfaz abstracta `RepositorioProductos`, desacoplándose del motor de persistencia.
- **`puertos/salida/repositorio_productos.py`**: Puerto de salida (`ABC`) con el contrato de persistencia (`guardar`, `buscar_por_id`, `buscar_por_codigo`, `listar_todos`, `actualizar`, `eliminar`).
- **`puertos/entrada/servicios_inventario.py`**: Puerto de entrada que define tres contratos adicionales:
  - `producto_tiene_stock(cantidad) -> bool`: recibe la cantidad y retorna un booleano.
  - `validar_stock_producto(producto_id) -> None`: recibe un parámetro y finaliza sin salida cuando es válido; lanza `ProductoSinStockError` cuando no hay unidades.
  - `generar_resumen_inventario() -> str`: no recibe parámetros y retorna un resumen textual.

Los tres casos de uso se implementan en `ServicioProductos` y reciben el repositorio
por inyección de dependencias. Por tanto, pueden probarse con un repositorio en
memoria o conectarse a otra infraestructura sin modificar la lógica de aplicación.

### 3. Infraestructura (`infrastructure/persistencia/`)
- **`modelo_producto.py`**: Modelo relacional `ProductoORM` para SQLAlchemy (`__tablename__ = 'productos'`).
- **`mapper_producto.py`**: Patrón Data Mapper (`MapperProducto`) para convertir bidireccionalmente entre la entidad pura del dominio `Producto` y el registro de base de datos `ProductoORM`.
- **`repositorio_productos_sqlalchemy.py`**: Implementación concreta del repositorio utilizando SQLAlchemy y SQLite.
- **`base_datos.py`**: Conexión a SQLite en memoria y fábrica de sesiones seguras. Usa `StaticPool` para compartir la misma base durante la ejecución.

### 4. Adaptadores de interfaz (`adapters/web/`)
- **`rutas.py`**: Controlador web Flask. Invoca únicamente los métodos de `ServicioProductos` y renderiza las plantillas Jinja2 con mensajes flash de éxito o error.
- **`templates/`**:
  - `base.html`: Maquetación común, navegación, alertas y modal de confirmación.
  - `productos.html`: Catálogo con contador total, barra de búsqueda, tabla responsive y estados vacíos.
  - `formulario_producto.html`: Formulario para registrar o modificar productos con validación.
- **`static/`**:
  - `estilos.css`: Interfaz moderna con la paleta solicitada (azul oscuro, azul medio, blanco, gris claro, verde para éxitos y rojo para errores).
  - `aplicacion.js`: Confirmación modal de eliminación, filtros dinámicos en vivo y cierre automático de notificaciones.

> Se mantienen módulos puente en `dominio/`, `aplicacion/`, `infraestructura/` y `presentacion/` para compatibilidad con imports previos.

---

## 🚀 Requisitos e Instalación

### Requisitos previos
- Python 3.10 o superior.

### 1. Clonar o acceder al proyecto
```bash
cd gestion_productos
```

### 2. Crear y activar entorno virtual
En Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

En Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

---

## 💻 Ejecución de la Aplicación

Para iniciar el servidor web:
```bash
python run.py
```

O especificando puerto personalizado:
```bash
python run.py --port 5000
```

Abre tu navegador en:
```
http://localhost:5000
```

> **Nota:** La base de datos SQLite en memoria y sus tablas se crean automáticamente al iniciar la aplicación. El inventario comienza vacío y se pierde al detener el proceso. Se puede sustituir mediante la variable `DATABASE_URL`.

---

## 🧪 Pruebas Automatizadas

El proyecto incluye una suite completa de pruebas unitarias y de integración desarrolladas con `pytest`:

```bash
pytest -v
```

### Cobertura de pruebas:
- ✅ Reglas de validación y límites en la entidad del dominio.
- ✅ Rechazo de códigos duplicados.
- ✅ Inyección de repositorio en memoria (Mocking/Stub sin base de datos).
- ✅ Persistencia real en base de datos SQLite aislada (`sqlite:///:memory:`).
- ✅ Traducción bidireccional mediante el Data Mapper.
- ✅ Pruebas de integración HTTP de la capa web Flask (GET, POST, redirecciones y mensajes flash).
