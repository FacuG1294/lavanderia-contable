# Sistema contable — Lavandería

App web simple para llevar los números del emprendimiento: ingresos, gastos,
reportes mensuales y un semáforo de facturación para el Monotributo.

## Qué incluye

- **Ingresos**: carga rápida por servicio (lavado, secado, planchado, combo,
  delivery), medio de pago y cliente opcional.
- **Gastos**: por categoría (insumos, alquiler, luz, agua, gas, sueldos,
  mantenimiento, impuestos, otro).
- **Panel principal**: balance del mes, gráfico de los últimos 6 meses, y un
  semáforo que muestra qué tan cerca está la facturación anual del tope de
  la categoría de Monotributo configurada.
- **Reportes**: por mes, con totales por categoría y exportación a CSV
  (se abre directo en Excel/Google Sheets).
- **Login simple**: un solo usuario/contraseña para vos y el dueño.

Los topes del Monotributo cargados corresponden a la tabla vigente desde el
1/08/2026 (ARCA). Se actualizan cada febrero y agosto — cuando salga una
nueva escala, avisame y actualizo `monotributo_data.py`.

## Probarlo en tu computadora

Necesitás Python 3.10+.

```bash
python3 -m venv venv
source venv/bin/activate        # en Windows: venv\Scripts\activate
pip install -r requirements.txt
python3 app.py
```

Abrí `http://localhost:5000`. Usuario y contraseña por defecto: `admin` / `admin123`
(se pueden cambiar con las variables de entorno `APP_USER` y `APP_PASS`, ver `.env.example`).

## Publicarlo online (gratis)

La forma más simple es **Render**:

1. Crear una cuenta en [render.com](https://render.com) y conectar tu repo de
   GitHub (subí esta carpeta a un repo nuevo primero).
2. "New +" → "Web Service" → elegir el repo.
3. Configuración:
   - Build command: `pip install -r requirements.txt`
   - Start command: `gunicorn app:app`
4. En "Environment" agregar las variables de `.env.example` con valores
   propios (`SECRET_KEY`, `APP_USER`, `APP_PASS`).
5. Deploy. Render te da una URL tipo `https://tu-lavanderia.onrender.com`.

Alternativas equivalentes: **Railway** (railway.app) o **PythonAnywhere**,
el proceso es muy similar (subir el código, definir el comando de arranque,
cargar variables de entorno).

### Importante sobre los datos

Esta versión guarda todo en un archivo SQLite (`lavanderia.db`) en el mismo
servidor. Funciona perfecto para un solo negocio, pero:

- En el plan gratuito de Render el disco **no es permanente**: si el servicio
  se reinicia, se puede perder la base. Para uso real conviene el plan pago
  con "persistent disk", o migrar a una base como PostgreSQL (Render y
  Railway ofrecen una gratis) — avisame si llegan a ese punto y lo adapto.
- Conviene bajar el CSV de reportes todos los meses como respaldo, o hacer
  backup del archivo `lavanderia.db` periódicamente.

## Estructura del proyecto

```
app.py                  backend Flask (rutas, lógica)
monotributo_data.py     tabla de categorías/topes del Monotributo
templates/              páginas HTML
static/style.css        estilos
requirements.txt        dependencias Python
Procfile                comando de arranque para el hosting
.env.example             variables de entorno de ejemplo
```

## Próximos pasos posibles

- Multi-usuario con permisos distintos (dueño vs. quien carga datos).
- Recordatorio automático del vencimiento del monotributo.
- Carga de comprobantes/fotos de gastos.
- Migrar a PostgreSQL si el negocio crece.
