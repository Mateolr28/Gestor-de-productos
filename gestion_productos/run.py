#!/usr/bin/env python3
"""
Punto de entrada principal para ejecutar la aplicación 'Gestor de Productos'.
Configura la inyección de dependencias conectando la infraestructura concreta
con el servicio de aplicación y la capa de presentación web.
"""

import os
import sys
import argparse

# Asegurar que el directorio raíz del proyecto esté en sys.path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from gestion_productos.infraestructura.base_datos import (
    obtener_motor,
    crear_fabrica_sesiones,
    inicializar_base_datos,
)
from gestion_productos.infraestructura.repositorio_productos_sqlalchemy import (
    RepositorioProductosSQLAlchemy,
)
from gestion_productos.aplicacion.servicio_productos import ServicioProductos
from gestion_productos.presentacion.rutas import crear_app


def construir_aplicacion(db_url: str = None):
    """
    Ensamblador de dependencias (Dependency Injection Container / Composition Root).
    1. Crea conexión a base de datos y sesión SQLite.
    2. Inicializa las tablas si no existen.
    3. Instancia el RepositorioProductosSQLAlchemy concreto.
    4. Inyecta el repositorio en el ServicioProductos.
    5. Inyecta el servicio en la aplicación Flask.
    """
    engine = obtener_motor(db_url)
    inicializar_base_datos(engine)
    session = crear_fabrica_sesiones(engine)

    repositorio = RepositorioProductosSQLAlchemy(session)
    servicio = ServicioProductos(repositorio)

    app = crear_app(servicio_productos=servicio)
    return app


def main():
    parser = argparse.ArgumentParser(description="Ejecutar servidor Gestor de Productos")
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("PORT", 5000)),
        help="Puerto en el que escuchará el servidor web (por defecto: 5000)",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="Dirección IP de escucha (por defecto: 0.0.0.0)",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Ejecutar en modo depuración de Flask",
    )
    args = parser.parse_args()

    app = construir_aplicacion()
    print("=" * 60)
    print("🚀 GESTOR DE PRODUCTOS (Arquitectura Desacoplada)")
    print(f"📡 Servidor iniciado en http://{args.host}:{args.port}")
    print("=" * 60)
    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
