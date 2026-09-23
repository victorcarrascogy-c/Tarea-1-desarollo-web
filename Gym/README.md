 # SportCross — Django MVT)

Sistema de gestión de gimnasio con autenticación, catálogo público tipo Sportlife y administración completa. Dominio aprobado: **Gimnasio**.

**Dominio y entidades (4):** `Plan` (membresías), `Socio` (clientes), `Clase` (Yoga/Running/Pesas + instructor), `Inscripción` (matrícula socio-clase). Relaciones: `Socio.plan FK PROTECT`, `Inscripción.socio FK CASCADE`, `Inscripción.clase FK PROTECT`.

## Modelo de datos y on_delete

| Modelo | Campos clave | Relación | on_delete | Justificación |
|---|---|---|---|---|
| **Plan** | nombre, precio, duracion_dias, `costo_diario()` | — | — | `costo_diario()` en modelo (`precio/duracion_dias`) cumple R4: regla de negocio en MODELO, no en vista. |
| **Socio** | nombre, rut `unique`, email, plan | `plan FK → Plan` | `PROTECT` | No se puede borrar un Plan si tiene socios matriculados (evita huérfanos y pérdida de ingresos). Admin debe reasignar/migrar socios antes. |
| **Clase** | nombre, instructor, capacidad_maxima | — | — | — |
| **Inscripción** | fecha_inscripcion, estado `ACTIVA/CANCELADA/FINALIZADA`, socio, clase | `socio FK → Socio` | `CASCADE` | Si se elimina el socio, se eliminan sus inscripciones (limpieza coherente, sin huérfanos). |
| | | `clase FK → Clase` | `PROTECT` | No se puede borrar una clase con inscripciones registradas (protege historial y ocupación). |

Cada modelo declara `__str__` y `Meta ordering` (`Plan precio`, `Socio nombre`, `Clase nombre`, `Inscripción -fecha_inscripcion`). Migración `Aplicaciones/Gimnasio/migrations/0001_initial.py` versionada.

## Arquitectura MVT

```
proyecto/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── Gym/ (settings.py, urls.py — delega con include())
└── Aplicaciones/Gimnasio/
    ├── models.py  (MODELO + reglas costo_diario, on_delete)
    ├── views.py   (VISTAS delgadas, coordinan)
    ├── urls.py    (rutas propias app)
    ├── admin.py   (list_display/list_filter/search_fields)
    ├── forms.py   (validación servidor)
    ├── migrations/
    ├── templates/Gimnasio/ (base.html + dashboard, planes, socios_list, socio_form, clases, inscripciones, detalle, login, cliente_home)
    └── static/Gimnasio/ (css/prototipo.css, js/validacion.js, js/prototipo.js)
```
`Gym/urls.py` delega con `include('Aplicaciones.Gimnasio.urls')`. Vistas delgadas, sin consultas en plantillas, `{% url %}` y `{% static %}` en todas.

## Motor PostgreSQL (no SQLite)

```bash
# requirements.txt
psycopg2-binary==2.9.13
python-dotenv==1.1.1
Django==5.2.17
```
Credenciales en `.env` (excluido en `.gitignore`), leídas en `Gym/settings.py` con `os.environ.get`. `.env.example` incluido.

**Script creación BD (README exigido):**
```sql
-- psql -U postgres
CREATE DATABASE "GYM" OWNER postgres;
CREATE USER gym_user WITH PASSWORD 'hola1234';
GRANT ALL PRIVILEGES ON DATABASE "GYM" TO gym_user;
-- o usar usuario postgres directo como en .env (DB_USER=postgres, DB_PASSWORD=hola1234, DB_HOST=localhost, DB_PORT=5432, DB_NAME=GYM)
```
Respaldo entregable: `pg_dump -U postgres -d GYM > respaldo.sql` (ver archivo `respaldo.sql` junto al repo).

## Autenticación y control de acceso

* Sistema `django.contrib.auth` (no contraseñas en modelo propio).
* `login.html` propia con estilo `#1E1E1E/#F8F9FA` (no default Django) en `/login/`, `logout` en menú (`/logout/`).
* Todas las vistas de gestión protegidas con `@login_required` (`socios/`, `clases/`, `inscripciones/`, `dashboard /`). Sin sesión → `302 /login/?next=`. Catálogo público `/planes/` y registro `/registro/` son públicos tipo Sportlife (documentado); gestión requiere login.
* Menú `base.html` muestra `Hola, {{user.username}}` y `Cerrar Sesión` cuando `is_authenticated`.
* `settings.py`: `LOGIN_URL='/login/'`, `LOGIN_REDIRECT_URL='/'`, `LOGOUT_REDIRECT_URL='/login/'`.

**Usuarios de prueba:**
| Usuario | Pass | Rol | RUT (cliente demo) |
|---|---|---|---|
| `admin` | `admin123` | superuser staff | — |
| `staff` | `staff123` | staff (crear con `createsuperuser`) | — |
| Cliente demo | — | Socio | `12.345.678-9` (Juan Pérez, Plan Anual) |

```bash
python manage.py createsuperuser  # admin/admin123 ya creado
```

## Flujos

* **Público Sportlife:** `GET /` → `302 /planes/` (catálogo 4 planes con `costo_diario`). Click `Seleccionar Plan` (borde azul `#2563EB` único) → `GET /registro/?plan=ID` → completa `nombre/rut/email + clase (Yoga/Running/Pesas, valida capacidad)` → `POST` crea `Socio + Inscripción ACTIVA` en BD → redirect `/planes/` con mensaje.
* **Admin:** `GET /login/` → login `admin/admin123` → `GET /` dashboard KPIs (Socios Activos, Ingresos `Sum(plan.precio)`, Capacidad `ACTIVA/capacidad_maxima`), `Planes más Vendidos`, `Próximas Clases`. CRUD `Socios` con filtro `?plan=Anual&q=12.3`, `Clases` ocupación real, `Inscripciones` filtrable y cambio estado `ACTIVA/CANCELADA/FINALIZADA` con verificación capacidad.

## Comandos para iniciar y migrations (guardados)

```bash
# 1) Instalar dependencias
pip install -r requirements.txt

# 2) Migrations — crear y aplicar (cada vez que cambias models.py)
python manage.py makemigrations          # genera Aplicaciones/Gimnasio/migrations/0002_*.py
python manage.py migrate                 # aplica en PostgreSQL GYM (no SQLite)
python manage.py showmigrations          # verifica [X] 0001_initial, 0002_...

# 3) Crear admin (para /login/ y /admin/)
python manage.py createsuperuser         # admin / admin123 ya creado

# 4) Iniciar servidor
python manage.py runserver               # http://127.0.0.1:8000/planes/ (público) | http://127.0.0.1:8000/login/ (admin)

# Otros útiles
python manage.py check                   # verifica MVT sin errores
python manage.py shell                   # probar ORM: from Aplicaciones.Gimnasio.models import Plan, Socio
```

## Instalación paso a paso (equipo limpio)

```bash
git clone <repo> && cd Gym
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env  # editar DB_NAME=GYM DB_USER=postgres DB_PASSWORD=hola1234 DB_HOST=localhost DB_PORT=5432
# crear BD
psql -U postgres -c "CREATE DATABASE \"GYM\";"
python manage.py migrate  # aplica 0001_initial en PostgreSQL (no SQLite)
python manage.py createsuperuser  # admin/admin123
# datos iniciales (opcional, ya en BD con 63 socios):
python manage.py shell -c "from Aplicaciones.Gimnasio.models import Plan, Clase; Plan.objects.get_or_create(nombre='Mensual', defaults={'precio':30000,'duracion_dias':30})"
python manage.py runserver
# http://127.0.0.1:8000/planes/ (público)  |  http://127.0.0.1:8000/login/ (admin)  |  http://127.0.0.1:8000/admin/
```

## Validación JS (4 tipos, archivo externo)

`static/Gimnasio/js/validacion.js` (no inline) valida antes de `submit` y muestra error junto al campo en español:
1. **Obligatorio** — nombre/rut/email/plan/clase no vacío
2. **Largo** — nombre ≥3 caracteres, rut ≥7
3. **Formato** — email `*@*.*`, RUT `XXXXXXXX-X` con puntos opcionales y dígito verificador `k/K`
4. **Selección obligatoria** — plan y clase `<select>` debe elegir opción (no placeholder)

Bloquea envío (`event.preventDefault()`) y pinta `border #DC2626 + bg #FEE2E2`. También valida `login` (usuario y contraseña obligatorios). Servidor mantiene validación en `forms.py` y `models.py` (unique, PROTECT).

## Admin y datos

`admin.py` registra 4 modelos con `list_display`, `list_filter`, `search_fields`, `ordering`, `list_select_related`. 63 socios + 62 inscripciones + 4 planes + 3 clases cargados (reales, no `aaa`). Ver `respaldo.sql`.

## Repositorio

`git log --oneline` debe mostrar aportes de ambos integrantes (no un único commit). `requirements.txt` vía `pip freeze > requirements.txt`, `.gitignore` excluye `venv/ __pycache__/ .env`.

## Defensa 10 min

Cada integrante debe explicar cualquier línea (`models.py:15 costo_diario`, `views.py:43 _ocupacion_por_clase`, `settings.py:20 load_dotenv`, `validacion.js:12 formato RUT`). Modificaciones en vivo de 2-3 min (ej: agregar campo, cambiar filtro, ajustar validación).
