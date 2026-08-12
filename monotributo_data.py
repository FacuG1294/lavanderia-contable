# Tabla de categorías del Monotributo (Argentina)
# Vigencia: desde el 1/08/2026 (actualización ARCA, ajuste 16,85%)
# Fuente: ARCA (ex AFIP) - https://www.afip.gob.ar/monotributo/categorias.asp
# Nota: estos valores se actualizan cada febrero y agosto. Hay que revisarlos
# y actualizarlos a mano cuando ARCA publique la nueva escala.

CATEGORIAS_MONOTRIBUTO = [
    {"cat": "A", "tope_anual": 12009410.45, "cuota_servicios": 49527.18},
    {"cat": "B", "tope_anual": 17595182.74, "cuota_servicios": 56379.08},
    {"cat": "C", "tope_anual": 24670494.31, "cuota_servicios": 66020.12},
    {"cat": "D", "tope_anual": 30628651.43, "cuota_servicios": 84612.93},
    {"cat": "E", "tope_anual": 36028231.33, "cuota_servicios": 119811.45},
    {"cat": "F", "tope_anual": 45151659.41, "cuota_servicios": 150784.21},
    {"cat": "G", "tope_anual": 53995798.87, "cuota_servicios": 230312.94},
    {"cat": "H", "tope_anual": 81924660.37, "cuota_servicios": 522706.68},
    # I, J, K existen pero son para categorías con empleados / venta de bienes,
    # muy por encima de lo esperable para una lavandería chica. Se agregan
    # igual por si hicieran falta.
    {"cat": "I", "tope_anual": 91699761.90, "cuota_servicios": 963747.86},
    {"cat": "J", "tope_anual": 105012519.20, "cuota_servicios": 1167299.76},
    {"cat": "K", "tope_anual": 126610838.75, "cuota_servicios": 1614446.04},
]

VIGENCIA = "1/08/2026"


def categoria_por_facturacion(monto_anual):
    """Devuelve la categoría mínima que corresponde a una facturación anual dada."""
    for c in CATEGORIAS_MONOTRIBUTO:
        if monto_anual <= c["tope_anual"]:
            return c
    return CATEGORIAS_MONOTRIBUTO[-1]


def get_categoria(codigo):
    for c in CATEGORIAS_MONOTRIBUTO:
        if c["cat"] == codigo:
            return c
    return None
