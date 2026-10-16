import os
import re
from flask import Flask, render_template, request, redirect, url_for, flash
from gestion_productos.aplicacion.servicio_productos import ServicioProductos
from gestion_productos.dominio.excepciones import (
    DominioError,
    ErrorValidacionProducto,
    ProductoNoEncontradoError,
    CodigoProductoDuplicadoError,
)


def parsear_precio(valor: str) -> float:
    """Convierte precios colombianos como ``1.000.000`` a un número."""
    texto = str(valor or "").strip().replace("$", "").replace(" ", "")
    if not texto:
        raise ErrorValidacionProducto("El precio debe ser un número válido.")

    if "," in texto:
        partes = texto.rsplit(",", 1)
        entero, decimal = partes
        if not decimal.isdigit() or len(decimal) > 2:
            raise ErrorValidacionProducto("El precio debe ser un número válido.")
        texto = entero.replace(".", "") + "." + decimal
    elif texto.count(".") > 1 or re.fullmatch(r"\d{1,3}(\.\d{3})+", texto):
        texto = texto.replace(".", "")

    try:
        return float(texto)
    except (ValueError, TypeError):
        raise ErrorValidacionProducto("El precio debe ser un número válido.")


def formato_pesos(valor) -> str:
    """Formatea un precio con separador de miles colombiano."""
    try:
        numero = float(valor)
    except (ValueError, TypeError):
        return ""

    texto = f"{numero:,.2f}"
    entero, decimal = texto.split(".")
    entero = entero.replace(",", ".")
    return entero if decimal == "00" else f"{entero},{decimal}"


def crear_app(servicio_productos: ServicioProductos = None) -> Flask:
    """
    Fábrica de la aplicación web Flask.
    Inyecta ServicioProductos en el contexto de presentación.
    Las rutas únicamente delegan casos de uso al servicio y presentan resultados.
    No ejecutan consultas SQL ni contienen reglas de validación de negocio.
    """
    templates_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")

    app = Flask(
        __name__,
        template_folder=templates_dir,
        static_folder=static_dir,
        static_url_path="/static",
    )
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "gestor-productos-clave-secreta-2026")
    app.jinja_env.filters["formato_pesos"] = formato_pesos

    # Almacenar referencia al servicio inyectado
    app.servicio_productos = servicio_productos

    @app.route("/")
    def index():
        """
        Vista principal: Lista los productos y soporta búsqueda opcional por código o nombre.
        Muestra también el conteo total de productos registrados.
        """
        servicio: ServicioProductos = app.servicio_productos
        termino_busqueda = request.args.get("q", "").strip()

        if termino_busqueda:
            productos = servicio.buscar_productos(termino_busqueda)
        else:
            productos = servicio.consultar_productos()

        total_productos = servicio.obtener_total_productos()

        return render_template(
            "productos.html",
            productos=productos,
            total_productos=total_productos,
            busqueda=termino_busqueda,
        )

    @app.route("/inventario")
    def inventario():
        """Muestra el resumen del inventario generado por la capa de aplicación."""
        servicio: ServicioProductos = app.servicio_productos
        resumen = servicio.generar_resumen_inventario()
        return render_template("inventario.html", resumen=resumen)

    @app.route("/productos/nuevo", methods=["GET", "POST"])
    def nuevo_producto():
        """
        Formulario y registro de un nuevo producto.
        """
        servicio: ServicioProductos = app.servicio_productos

        if request.method == "POST":
            codigo = request.form.get("codigo", "").strip()
            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            precio_raw = request.form.get("precio", "").strip()
            cantidad_raw = request.form.get("cantidad", "").strip()

            datos_formulario = {
                "codigo": codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "precio": precio_raw,
                "cantidad": cantidad_raw,
            }

            try:
                # Conversión básica de tipos antes de llamar al servicio
                precio = parsear_precio(precio_raw)

                try:
                    cantidad = int(cantidad_raw)
                except (ValueError, TypeError):
                    raise ErrorValidacionProducto("La cantidad debe ser un número entero.")

                servicio.registrar_producto(
                    codigo=codigo,
                    nombre=nombre,
                    precio=precio,
                    cantidad=cantidad,
                    descripcion=descripcion,
                )
                flash(f"Producto '{nombre}' ({codigo}) registrado exitosamente.", "exito")
                return redirect(url_for("index"))

            except (ErrorValidacionProducto, CodigoProductoDuplicadoError) as err:
                flash(str(err), "error")
                return render_template(
                    "formulario_producto.html",
                    modo="crear",
                    producto=datos_formulario,
                )
            except Exception as e:
                flash(f"Ocurrió un error inesperado: {str(e)}", "error")
                return render_template(
                    "formulario_producto.html",
                    modo="crear",
                    producto=datos_formulario,
                )

        return render_template(
            "formulario_producto.html",
            modo="crear",
            producto={},
        )

    @app.route("/productos/<int:producto_id>/editar", methods=["GET", "POST"])
    def editar_producto(producto_id: int):
        """
        Formulario y actualización de un producto existente.
        """
        servicio: ServicioProductos = app.servicio_productos

        try:
            producto = servicio.obtener_producto_por_id(producto_id)
        except ProductoNoEncontradoError as err:
            flash(str(err), "error")
            return redirect(url_for("index"))

        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            descripcion = request.form.get("descripcion", "").strip()
            precio_raw = request.form.get("precio", "").strip()
            cantidad_raw = request.form.get("cantidad", "").strip()

            datos_formulario = {
                "id": producto.id,
                "codigo": producto.codigo,
                "nombre": nombre,
                "descripcion": descripcion,
                "precio": precio_raw,
                "cantidad": cantidad_raw,
            }

            try:
                precio = parsear_precio(precio_raw)

                try:
                    cantidad = int(cantidad_raw)
                except (ValueError, TypeError):
                    raise ErrorValidacionProducto("La cantidad debe ser un número entero.")

                servicio.actualizar_producto(
                    producto_id=producto_id,
                    nombre=nombre,
                    descripcion=descripcion,
                    precio=precio,
                    cantidad=cantidad,
                )
                flash(f"Producto '{nombre}' actualizado correctamente.", "exito")
                return redirect(url_for("index"))

            except (ErrorValidacionProducto, ProductoNoEncontradoError) as err:
                flash(str(err), "error")
                return render_template(
                    "formulario_producto.html",
                    modo="editar",
                    producto=datos_formulario,
                )
            except Exception as e:
                flash(f"Ocurrió un error inesperado al actualizar: {str(e)}", "error")
                return render_template(
                    "formulario_producto.html",
                    modo="editar",
                    producto=datos_formulario,
                )

        return render_template(
            "formulario_producto.html",
            modo="editar",
            producto=producto,
        )

    @app.route("/productos/<int:producto_id>/eliminar", methods=["POST"])
    def eliminar_producto(producto_id: int):
        """
        Eliminación controlada de un producto con confirmación previa.
        """
        servicio: ServicioProductos = app.servicio_productos

        try:
            servicio.eliminar_producto(producto_id)
            flash("Producto eliminado exitosamente del inventario.", "exito")
        except ProductoNoEncontradoError as err:
            flash(str(err), "error")
        except Exception as e:
            flash(f"No fue posible eliminar el producto: {str(e)}", "error")

        return redirect(url_for("index"))

    @app.errorhandler(404)
    def pagina_no_encontrada(e):
        flash("La página o recurso solicitado no existe.", "error")
        return redirect(url_for("index"))

    @app.errorhandler(500)
    def error_interno(e):
        flash("Ocurrió un error interno en el servidor. Intente nuevamente.", "error")
        return redirect(url_for("index"))

    return app
