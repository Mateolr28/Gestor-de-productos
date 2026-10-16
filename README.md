# Gestor de Productos

Sistema sencillo de gestión de productos desarrollado con **Python**, **Flask**, **SQLAlchemy** y **SQLite**, diseñado bajo una **arquitectura desacoplada** para demostrar de forma limpia y académica los principios de separación de responsabilidades, contratos de interfaz, inversión de dependencias y el patrón Data Mapper.

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

### 1. Dominio (`gestion_productos/dominio/`)
- **`producto.py`**: Entidad `Producto` pura. Encapsula los atributos comerciales (`codigo`, `nombre`, `precio`, `cantidad`, `descripcion`, `fecha_registro`) y valida sus invariantes (campos obligatorios, precio $\ge 0$, cantidad entera $\ge 0$). **No importa Flask, ni SQLAlchemy, ni SQLite**.
- **`interfaces/repositorio_productos.py`**: Interfaz abstracta (`ABC`) que establece el contrato formal para operaciones de almacenamiento (`guardar`, `buscar_por_id`, `buscar_por_codigo`, `listar_todos`, `actualizar`, `eliminar`).
- **`excepciones.py`**: Jerarquía de excepciones de negocio (`ErrorValidacionProducto`, `ProductoNoEncontradoError`, `CodigoProductoDuplicadoError`).

### 2. Aplicación (`gestion_productos/aplicacion/`)
- **`servicio_productos.py`**: Clase `ServicioProductos` que orquesta los casos de uso:
  - Registro de productos verificando unicidad de código.
  - Consulta y búsqueda por nombre o código.
  - Actualización de datos comerciales.
  - Eliminación con validación de existencia.
  - Inyección de dependencias: solo conoce la interfaz abstracta `RepositorioProductos`, desacoplándose del motor de persistencia.

### 3. Infraestructura (`gestion_productos/infraestructura/`)
- **`modelo_producto.py`**: Modelo relacional `ProductoORM` para SQLAlchemy (`__tablename__ = 'productos'`).
- **`mapper_producto.py`**: Patrón Data Mapper (`MapperProducto`) para convertir bidireccionalmente entre la entidad pura del dominio `Producto` y el registro de base de datos `ProductoORM`.
- **`repositorio_productos_sqlalchemy.py`**: Implementación concreta del repositorio utilizando SQLAlchemy y SQLite.
- **`base_datos.py`**: Conexión a SQLite y fábrica de sesiones seguras.

### 4. Presentación (`gestion_productos/presentacion/`)
- **`rutas.py`**: Controlador web Flask. Invoca únicamente los métodos de `ServicioProductos` y renderiza las plantillas Jinja2 con mensajes flash de éxito o error.
- **`templates/`**:
  - `base.html`: Maquetación común, navegación, alertas y modal de confirmación.
  - `productos.html`: Catálogo con contador total, barra de búsqueda, tabla responsive y estados vacíos.
  - `formulario_producto.html`: Formulario para registrar o modificar productos con validación.
- **`static/`**:
  - `estilos.css`: Interfaz moderna con la paleta solicitada (azul oscuro, azul medio, blanco, gris claro, verde para éxitos y rojo para errores).
  - `aplicacion.js`: Confirmación modal de eliminación, filtros dinámicos en vivo y cierre automático de notificaciones.

---

## 🚀 Requisitos e Instalación

### Requisitos previos
- Python 3.10 o superior.

### 1. Crear y activar entorno virtual
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

### 2. Instalar dependencias
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
