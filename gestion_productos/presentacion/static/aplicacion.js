/**
 * Gestor de Productos - Lógica frontend vanilla (JavaScript)
 * Manejo accesible del modal de confirmación, validación de formularios y filtros rápidos.
 */

document.addEventListener('DOMContentLoaded', () => {
    inicializarAlertas();
    inicializarFiltroEnVivo();
    inicializarTecladoModal();
    inicializarFormatoPrecios();
});

/**
 * Formatea el precio con puntos de miles mientras se escribe.
 * La coma se reserva para los centavos: 1.000.000,50.
 */
function inicializarFormatoPrecios() {
    const input = document.getElementById('precio');
    if (!input) return;

    const formatear = () => {
        const valor = input.value.replace(/[^\d,]/g, '');
        const partes = valor.split(',');
        const entero = (partes[0] || '').replace(/^0+(?=\d)/, '');
        const decimal = partes.length > 1 ? `,${partes[1].slice(0, 2)}` : '';

        // Agrupar manualmente evita que Number() altere o valor durante la escritura.
        const enteroFormateado = entero.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
        input.value = entero ? `${enteroFormateado}${decimal}` : '';
    };

    input.addEventListener('input', formatear);
}

/**
 * Cierra automáticamente las alertas de éxito luego de 5 segundos.
 */
function inicializarAlertas() {
    const alerts = document.querySelectorAll('.alert-exito');
    alerts.forEach((alert) => {
        setTimeout(() => {
            if (alert && alert.parentElement) {
                alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
                alert.style.opacity = '0';
                alert.style.transform = 'translateY(-6px)';
                setTimeout(() => alert.remove(), 400);
            }
        }, 5000);
    });
}

/**
 * Abre el modal de confirmación para eliminar un producto.
 * @param {string|number} id - ID del producto en base de datos.
 * @param {string} nombre - Nombre del producto.
 * @param {string} codigo - Código del producto.
 */
function abrirModalEliminar(id, nombre, codigo) {
    const modal = document.getElementById('modalEliminar');
    const form = document.getElementById('formConfirmarEliminar');
    const nombreElem = document.getElementById('modalNombreProducto');
    const codigoElem = document.getElementById('modalCodigoProducto');

    if (!modal || !form) return;

    form.action = `/productos/${id}/eliminar`;
    if (nombreElem) nombreElem.textContent = nombre;
    if (codigoElem) codigoElem.textContent = codigo;

    modal.style.display = 'flex';
    document.body.style.overflow = 'hidden'; // Evita scroll de fondo
}

/**
 * Cierra el modal de confirmación para eliminar.
 */
function cerrarModalEliminar() {
    const modal = document.getElementById('modalEliminar');
    if (!modal) return;

    modal.style.display = 'none';
    document.body.style.overflow = '';
}

/**
 * Cierra el modal con la tecla Escape o haciendo clic fuera del diálogo.
 */
function inicializarTecladoModal() {
    const modal = document.getElementById('modalEliminar');
    if (!modal) return;

    // Clic fuera del contenido
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            cerrarModalEliminar();
        }
    });

    // Tecla Escape
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal.style.display === 'flex') {
            cerrarModalEliminar();
        }
    });
}

/**
 * Filtro interactivo en vivo en la tabla de productos si el usuario escribe en el input.
 */
function inicializarFiltroEnVivo() {
    const input = document.getElementById('inputBusqueda');
    const tabla = document.getElementById('tablaProductos');
    if (!input || !tabla) return;

    const filas = tabla.querySelectorAll('tbody tr.table-row');
    if (!filas.length) return;

    input.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();

        let visibles = 0;
        filas.forEach((fila) => {
            const codigo = fila.getAttribute('data-codigo') || '';
            const nombre = fila.getAttribute('data-nombre') || '';

            if (!query || codigo.includes(query) || nombre.includes(query)) {
                fila.style.display = '';
                visibles++;
            } else {
                fila.style.display = 'none';
            }
        });

        // Actualizar el contador dinámico en pantalla
        const contador = document.getElementById('contadorProductos');
        if (contador) {
            contador.textContent = query ? visibles : filas.length;
        }
    });
}
