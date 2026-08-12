# Tabla de categorías del Monotributo (Argentina) - actividad "Servicios"
# Vigencia: desde el 1/08/2026 (actualización ARCA, ajuste 16,85%)
# Fuente: ARCA (ex AFIP) - https://www.afip.gob.ar/monotributo/categorias.asp
# Nota: estos valores se actualizan cada febrero y agosto. Cuando salga una
# escala nueva hay que revisar y actualizar esta tabla a mano.
#
# imp_integrado = impuesto integrado (la parte "impositiva")
# aporte_sipa   = aporte jubilatorio (SIPA)
# aporte_os     = aporte a la obra social
# cuota_servicios = suma de los tres (columna de referencia / compatibilidad)

CATEGORIAS_MONOTRIBUTO = [
    {"cat": "A", "tope_anual": 12009410.45, "imp_integrado": 5585.77,   "aporte_sipa": 18246.86,  "aporte_os": 25694.55, "cuota_servicios": 49527.18},
    {"cat": "B", "tope_anual": 17595182.74, "imp_integrado": 10612.98,  "aporte_sipa": 20071.55,  "aporte_os": 25694.55, "cuota_servicios": 56379.08},
    {"cat": "C", "tope_anual": 24670494.31, "imp_integrado": 18246.86,  "aporte_sipa": 22078.71,  "aporte_os": 25694.55, "cuota_servicios": 66020.12},
    {"cat": "D", "tope_anual": 30628651.43, "imp_integrado": 29790.79,  "aporte_sipa": 24286.58,  "aporte_os": 30535.56, "cuota_servicios": 84612.93},
    {"cat": "E", "tope_anual": 36028231.33, "imp_integrado": 55857.73,  "aporte_sipa": 26715.24,  "aporte_os": 37238.48, "cuota_servicios": 119811.45},
    {"cat": "F", "tope_anual": 45151659.41, "imp_integrado": 78573.20,  "aporte_sipa": 29386.76,  "aporte_os": 42824.25, "cuota_servicios": 150784.21},
    {"cat": "G", "tope_anual": 53995798.87, "imp_integrado": 142995.76, "aporte_sipa": 41141.46,  "aporte_os": 46175.72, "cuota_servicios": 230312.94},
    {"cat": "H", "tope_anual": 81924660.37, "imp_integrado": 409623.31, "aporte_sipa": 57598.04,  "aporte_os": 55485.33, "cuota_servicios": 522706.68},
    # I, J, K existen pero son para categorias con empleados / venta de
    # bienes, muy por encima de lo esperable para una lavanderia chica.
    {"cat": "I", "tope_anual": 91699761.90,  "imp_integrado": 814591.79,   "aporte_sipa": 80637.26,  "aporte_os": 68518.81, "cuota_servicios": 963747.86},
    {"cat": "J", "tope_anual": 105012519.20, "imp_integrado": 977510.14,   "aporte_sipa": 112892.16, "aporte_os": 76897.46, "cuota_servicios": 1167299.76},
    {"cat": "K", "tope_anual": 126610838.75, "imp_integrado": 1368514.20,  "aporte_sipa": 158049.02, "aporte_os": 87882.82, "cuota_servicios": 1614446.04},
]

VIGENCIA = "1/08/2026"

MESES_ES = {
    1: "ene", 2: "feb", 3: "mar", 4: "abr", 5: "may", 6: "jun",
    7: "jul", 8: "ago", 9: "sep", 10: "oct", 11: "nov", 12: "dic",
}


def categoria_por_facturacion(monto_anual):
    """Devuelve la categoria minima que corresponde a una facturacion anual dada."""
    for c in CATEGORIAS_MONOTRIBUTO:
        if monto_anual <= c["tope_anual"]:
            return c
    return CATEGORIAS_MONOTRIBUTO[-1]


def get_categoria(codigo):
    for c in CATEGORIAS_MONOTRIBUTO:
        if c["cat"] == codigo:
            return c
    return None


def periodo_legible(periodo):
    """'2026-08' -> 'ago-2026'"""
    try:
        y, m = periodo.split("-")
        return f"{MESES_ES[int(m)]}-{y}"
    except Exception:
        return periodo
