import os
import sqlite3
from datetime import datetime, date
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, Response, g
)

from monotributo_data import CATEGORIAS_MONOTRIBUTO, categoria_por_facturacion, get_categoria, VIGENCIA

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "lavanderia.db")

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "cambiar-esta-clave-en-produccion")

APP_USER = os.environ.get("APP_USER", "admin")
APP_PASS = os.environ.get("APP_PASS", "admin123")

INGRESO_CATEGORIAS = ["Lavado", "Secado", "Planchado", "Combo (lavado+secado)", "Delivery", "Otro"]
GASTO_CATEGORIAS = ["Insumos", "Alquiler", "Luz", "Agua", "Gas", "Sueldos", "Mantenimiento", "Monotributo/Impuestos", "Otro"]
MEDIOS_PAGO = ["Efectivo", "Transferencia", "Tarjeta debito", "Tarjeta credito", "Billetera virtual"]


# ---------- DB ----------

def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DB_PATH)
    db.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL CHECK(tipo IN ('ingreso','gasto')),
            fecha TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            medio_pago TEXT,
            contraparte TEXT,
            nota TEXT,
            creado_en TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    """)
    db.commit()
    db.close()


def get_setting(key, default=None):
    db = get_db()
    row = db.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default


def set_setting(key, value):
    db = get_db()
    db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
        (key, value),
    )
    db.commit()


# ---------- Auth ----------

def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login", next=request.path))
        return f(*args, **kwargs)
    return wrapper


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "")
        pw = request.form.get("password", "")
        if user == APP_USER and pw == APP_PASS:
            session["logged_in"] = True
            session["username"] = user
            nxt = request.args.get("next") or url_for("dashboard")
            return redirect(nxt)
        flash("Usuario o contraseña incorrectos", "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ---------- Helpers ----------

def parse_month(month_str):
    """month_str formato YYYY-MM. Devuelve (year, month) o mes actual si invalido."""
    try:
        y, m = month_str.split("-")
        return int(y), int(m)
    except Exception:
        today = date.today()
        return today.year, today.month


def month_bounds(year, month):
    start = f"{year:04d}-{month:02d}-01"
    if month == 12:
        end = f"{year + 1:04d}-01-01"
    else:
        end = f"{year:04d}-{month + 1:02d}-01"
    return start, end


# ---------- Rutas ----------

@app.route("/")
@login_required
def dashboard():
    db = get_db()
    today = date.today()
    year, month = today.year, today.month
    start, end = month_bounds(year, month)

    ingresos_mes = db.execute(
        "SELECT COALESCE(SUM(monto),0) AS total FROM transactions WHERE tipo='ingreso' AND fecha >= ? AND fecha < ?",
        (start, end),
    ).fetchone()["total"]

    gastos_mes = db.execute(
        "SELECT COALESCE(SUM(monto),0) AS total FROM transactions WHERE tipo='gasto' AND fecha >= ? AND fecha < ?",
        (start, end),
    ).fetchone()["total"]

    # Facturacion acumulada ultimos 12 meses (para el semaforo de monotributo)
    hace_12 = today.replace(year=today.year - 1) if not (today.month == 2 and today.day == 29) else today.replace(year=today.year - 1, day=28)
    facturacion_12m = db.execute(
        "SELECT COALESCE(SUM(monto),0) AS total FROM transactions WHERE tipo='ingreso' AND fecha >= ?",
        (hace_12.isoformat(),),
    ).fetchone()["total"]

    categoria_actual = get_setting("categoria_monotributo", "B")
    cat_info = get_categoria(categoria_actual) or CATEGORIAS_MONOTRIBUTO[1]
    porcentaje_tope = (facturacion_12m / cat_info["tope_anual"] * 100) if cat_info["tope_anual"] else 0
    categoria_sugerida = categoria_por_facturacion(facturacion_12m)

    ultimos_mov = db.execute(
        "SELECT * FROM transactions ORDER BY fecha DESC, id DESC LIMIT 8"
    ).fetchall()

    # datos para grafico de los ultimos 6 meses
    meses_labels = []
    meses_ingresos = []
    meses_gastos = []
    y, m = year, month
    periodos = []
    for i in range(5, -1, -1):
        yy, mm = year, month - i
        while mm <= 0:
            mm += 12
            yy -= 1
        periodos.append((yy, mm))
    for yy, mm in periodos:
        s, e = month_bounds(yy, mm)
        ing = db.execute(
            "SELECT COALESCE(SUM(monto),0) t FROM transactions WHERE tipo='ingreso' AND fecha >= ? AND fecha < ?",
            (s, e),
        ).fetchone()["t"]
        gas = db.execute(
            "SELECT COALESCE(SUM(monto),0) t FROM transactions WHERE tipo='gasto' AND fecha >= ? AND fecha < ?",
            (s, e),
        ).fetchone()["t"]
        meses_labels.append(f"{mm:02d}/{yy}")
        meses_ingresos.append(ing)
        meses_gastos.append(gas)

    return render_template(
        "dashboard.html",
        ingresos_mes=ingresos_mes,
        gastos_mes=gastos_mes,
        balance_mes=ingresos_mes - gastos_mes,
        facturacion_12m=facturacion_12m,
        cat_info=cat_info,
        categoria_actual=categoria_actual,
        porcentaje_tope=porcentaje_tope,
        categoria_sugerida=categoria_sugerida,
        ultimos_mov=ultimos_mov,
        meses_labels=meses_labels,
        meses_ingresos=meses_ingresos,
        meses_gastos=meses_gastos,
        vigencia=VIGENCIA,
    )


@app.route("/ingresos", methods=["GET", "POST"])
@login_required
def ingresos():
    db = get_db()
    if request.method == "POST":
        try:
            monto = float(request.form.get("monto", "0").replace(",", "."))
        except ValueError:
            flash("Monto invalido", "error")
            return redirect(url_for("ingresos"))
        db.execute(
            "INSERT INTO transactions (tipo, fecha, categoria, monto, medio_pago, contraparte, nota, creado_en) "
            "VALUES ('ingreso', ?, ?, ?, ?, ?, ?, ?)",
            (
                request.form.get("fecha") or date.today().isoformat(),
                request.form.get("categoria"),
                monto,
                request.form.get("medio_pago"),
                request.form.get("contraparte", ""),
                request.form.get("nota", ""),
                datetime.now().isoformat(),
            ),
        )
        db.commit()
        flash("Ingreso registrado", "success")
        return redirect(url_for("ingresos"))

    filas = db.execute(
        "SELECT * FROM transactions WHERE tipo='ingreso' ORDER BY fecha DESC, id DESC LIMIT 100"
    ).fetchall()
    return render_template(
        "movimientos.html",
        tipo="ingreso",
        titulo="Ingresos",
        categorias=INGRESO_CATEGORIAS,
        medios_pago=MEDIOS_PAGO,
        filas=filas,
        hoy=date.today().isoformat(),
    )


@app.route("/gastos", methods=["GET", "POST"])
@login_required
def gastos():
    db = get_db()
    if request.method == "POST":
        try:
            monto = float(request.form.get("monto", "0").replace(",", "."))
        except ValueError:
            flash("Monto invalido", "error")
            return redirect(url_for("gastos"))
        db.execute(
            "INSERT INTO transactions (tipo, fecha, categoria, monto, medio_pago, contraparte, nota, creado_en) "
            "VALUES ('gasto', ?, ?, ?, ?, ?, ?, ?)",
            (
                request.form.get("fecha") or date.today().isoformat(),
                request.form.get("categoria"),
                monto,
                request.form.get("medio_pago"),
                request.form.get("contraparte", ""),
                request.form.get("nota", ""),
                datetime.now().isoformat(),
            ),
        )
        db.commit()
        flash("Gasto registrado", "success")
        return redirect(url_for("gastos"))

    filas = db.execute(
        "SELECT * FROM transactions WHERE tipo='gasto' ORDER BY fecha DESC, id DESC LIMIT 100"
    ).fetchall()
    return render_template(
        "movimientos.html",
        tipo="gasto",
        titulo="Gastos",
        categorias=GASTO_CATEGORIAS,
        medios_pago=MEDIOS_PAGO,
        filas=filas,
        hoy=date.today().isoformat(),
    )


@app.route("/movimientos/<int:mov_id>/eliminar", methods=["POST"])
@login_required
def eliminar_movimiento(mov_id):
    db = get_db()
    row = db.execute("SELECT tipo FROM transactions WHERE id = ?", (mov_id,)).fetchone()
    db.execute("DELETE FROM transactions WHERE id = ?", (mov_id,))
    db.commit()
    flash("Movimiento eliminado", "success")
    if row and row["tipo"] == "gasto":
        return redirect(url_for("gastos"))
    return redirect(url_for("ingresos"))


@app.route("/reportes", methods=["GET"])
@login_required
def reportes():
    db = get_db()
    month_str = request.args.get("mes", date.today().strftime("%Y-%m"))
    year, month = parse_month(month_str)
    start, end = month_bounds(year, month)

    ingresos_por_cat = db.execute(
        "SELECT categoria, SUM(monto) total, COUNT(*) cant FROM transactions "
        "WHERE tipo='ingreso' AND fecha >= ? AND fecha < ? GROUP BY categoria ORDER BY total DESC",
        (start, end),
    ).fetchall()

    gastos_por_cat = db.execute(
        "SELECT categoria, SUM(monto) total, COUNT(*) cant FROM transactions "
        "WHERE tipo='gasto' AND fecha >= ? AND fecha < ? GROUP BY categoria ORDER BY total DESC",
        (start, end),
    ).fetchall()

    total_ingresos = sum(r["total"] for r in ingresos_por_cat)
    total_gastos = sum(r["total"] for r in gastos_por_cat)

    movimientos = db.execute(
        "SELECT * FROM transactions WHERE fecha >= ? AND fecha < ? ORDER BY fecha, id",
        (start, end),
    ).fetchall()

    return render_template(
        "reportes.html",
        mes_actual=f"{year:04d}-{month:02d}",
        ingresos_por_cat=ingresos_por_cat,
        gastos_por_cat=gastos_por_cat,
        total_ingresos=total_ingresos,
        total_gastos=total_gastos,
        balance=total_ingresos - total_gastos,
        movimientos=movimientos,
    )


@app.route("/reportes/exportar.csv")
@login_required
def exportar_csv():
    db = get_db()
    month_str = request.args.get("mes", date.today().strftime("%Y-%m"))
    year, month = parse_month(month_str)
    start, end = month_bounds(year, month)
    filas = db.execute(
        "SELECT fecha, tipo, categoria, monto, medio_pago, contraparte, nota FROM transactions "
        "WHERE fecha >= ? AND fecha < ? ORDER BY fecha, id",
        (start, end),
    ).fetchall()

    lines = ["fecha,tipo,categoria,monto,medio_pago,contraparte,nota"]
    for f in filas:
        nota = (f["nota"] or "").replace(",", ";").replace("\n", " ")
        contraparte = (f["contraparte"] or "").replace(",", ";")
        lines.append(
            f'{f["fecha"]},{f["tipo"]},{f["categoria"]},{f["monto"]},{f["medio_pago"] or ""},{contraparte},{nota}'
        )
    csv_data = "\n".join(lines)
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename=reporte_{year:04d}-{month:02d}.csv"},
    )


@app.route("/config", methods=["GET", "POST"])
@login_required
def config():
    if request.method == "POST":
        set_setting("nombre_negocio", request.form.get("nombre_negocio", ""))
        set_setting("categoria_monotributo", request.form.get("categoria_monotributo", "B"))
        flash("Configuracion guardada", "success")
        return redirect(url_for("config"))

    return render_template(
        "config.html",
        nombre_negocio=get_setting("nombre_negocio", "Tifon Lavanderia"),
        categoria_actual=get_setting("categoria_monotributo", "B"),
        categorias=CATEGORIAS_MONOTRIBUTO,
        vigencia=VIGENCIA,
    )


@app.context_processor
def inject_globals():
    return {"nombre_negocio": get_setting("nombre_negocio", "Tifon Lavanderia") if session.get("logged_in") else ""}


init_db()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=os.environ.get("FLASK_DEBUG", "0") == "1")
