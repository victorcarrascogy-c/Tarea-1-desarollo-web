from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum, Q
from django import forms as django_forms
from django.utils import timezone
from datetime import date
from .models import Plan, Socio, Clase, Inscripcion
from .forms import SocioForm, InscripcionForm, ClaseForm, PlanForm

# ---------- helpers ----------
def _is_cliente(request):
    return 'cliente_socio_id' in request.session

def _get_cliente(request):
    sid = request.session.get('cliente_socio_id')
    if sid:
        try:
            return Socio.objects.select_related('plan').get(pk=sid)
        except Socio.DoesNotExist:
            pass
    return None

def _kpis():
    socios_activos = Socio.objects.count()
    hoy = date.today()
    inscripciones_hoy = Inscripcion.objects.filter(fecha_inscripcion=hoy).count()
    ingresos = Socio.objects.aggregate(total=Sum('plan__precio'))['total'] or 0
    clases = Clase.objects.all()
    total_capacidad = sum(c.capacidad_maxima for c in clases) or 1
    ocupados = Inscripcion.objects.filter(estado='ACTIVA').count()
    capacidad_pct = round(ocupados / total_capacidad * 100) if total_capacidad else 0
    return {
        'socios_activos': socios_activos,
        'inscripciones_hoy': inscripciones_hoy,
        'ingresos_estimados': ingresos,
        'capacidad_pct': capacidad_pct,
        'ocupados': ocupados,
        'total_capacidad': total_capacidad,
    }

def _ocupacion_por_clase():
    clases = Clase.objects.all().order_by('nombre')
    ocup_map = dict(Inscripcion.objects.filter(estado='ACTIVA').values('clase').annotate(c=Count('id')).values_list('clase','c'))
    data=[]
    for c in clases:
        ocup = ocup_map.get(c.id, 0)
        pct = round(ocup / c.capacidad_maxima * 100) if c.capacidad_maxima else 0
        data.append({'obj': c, 'ocupados': ocup, 'pct': pct, 'libres': c.capacidad_maxima - ocup, 'lleno': ocup >= c.capacidad_maxima})
    return data

# ---------- login solo admin (esquina) — 2 ventanas: compra publica + login admin ----------
def login_view(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('Gimnasio:home')
    error_admin = None
    if request.method == 'POST':
        username = request.POST.get('username','').strip()
        password = request.POST.get('password','')
        user = authenticate(request, username=username, password=password)
        if user and user.is_staff:
            login(request, user)
            messages.success(request, f'Bienvenido Admin {user.username}')
            return redirect('Gimnasio:home')
        else:
            error_admin = 'Credenciales inválidas o no es admin.'
    return render(request, 'Gimnasio/login.html', {'error_admin': error_admin})

def logout_view(request):
    logout(request)
    request.session.pop('cliente_socio_id', None)
    request.session.pop('cliente_nombre', None)
    messages.success(request, 'Sesión cerrada.')
    return redirect('Gimnasio:login')

# ---------- decorador cliente ----------
def cliente_required(view):
    def wrapper(request, *args, **kwargs):
        if not _is_cliente(request):
            messages.error(request, 'Debes ingresar con tu RUT como cliente.')
            return redirect('Gimnasio:login')
        return view(request, *args, **kwargs)
    return wrapper

# ---------- cliente home (solo pagar plan) ----------
@cliente_required
def cliente_home(request):
    socio = _get_cliente(request)
    inscripciones = Inscripcion.objects.filter(socio=socio).select_related('clase').order_by('-fecha_inscripcion')
    clases_disponibles = Clase.objects.all().order_by('nombre')
    ultimo_pago = request.session.get(f'pago_{socio.pk}', None)
    return render(request, 'Gimnasio/cliente_home.html', {'socio': socio, 'inscripciones': inscripciones, 'clases_disponibles': clases_disponibles, 'ultimo_pago': ultimo_pago})

@cliente_required
def cliente_pagar(request):
    socio = _get_cliente(request)
    if request.method == 'POST':
        # simular pago: guardar timestamp
        import datetime
        request.session[f'pago_{socio.pk}'] = datetime.datetime.now().strftime('%d/%m/%Y %H:%M')
        messages.success(request, f'Pago confirmado — Plan {socio.plan.nombre} ${socio.plan.precio} pagado. ¡Gracias {socio.nombre}!')
        return redirect('Gimnasio:cliente_home')
    return render(request, 'Gimnasio/cliente_pagar.html', {'socio': socio})

@cliente_required
def cliente_inscribir(request):
    socio = _get_cliente(request)
    if request.method == 'POST':
        clase_id = request.POST.get('clase')
        clase = get_object_or_404(Clase, pk=clase_id)
        ocup = Inscripcion.objects.filter(clase=clase, estado='ACTIVA').count()
        if ocup >= clase.capacidad_maxima:
            messages.error(request, f'{clase.nombre} está llena ({ocup}/{clase.capacidad_maxima}).')
        else:
            Inscripcion.objects.create(socio=socio, clase=clase, estado='ACTIVA')
            messages.success(request, f'Inscrito en {clase.nombre} con {clase.instructor}.')
        return redirect('Gimnasio:cliente_home')
    return redirect('Gimnasio:cliente_home')

# ---------- admin views ----------
def home(request):
    # Página principal = planes público tipo Sportlife. Si es admin, ve dashboard; si no, ve catálogo.
    if request.user.is_authenticated and request.user.is_staff:
        kpis = _kpis()
        planes_rank = Plan.objects.annotate(ventas=Count('socio')).order_by('-ventas')
        ocupacion = _ocupacion_por_clase()
        return render(request, 'Gimnasio/dashboard.html', {**kpis, 'planes_rank': planes_rank, 'ocupacion': ocupacion})
    # público — muestra planes como landing principal
    planes = Plan.objects.all().order_by('precio')
    return render(request, 'Gimnasio/planes.html', {'planes': planes})

def prototipo(request):
    planes = Plan.objects.all().order_by('precio')
    clases = Clase.objects.all().order_by('nombre')
    socios = Socio.objects.select_related('plan').all()
    inscripciones = Inscripcion.objects.select_related('socio', 'clase').all()
    return render(request, 'Gimnasio/prototipo.html', {'planes': planes, 'clases': clases, 'socios': socios, 'inscripciones': inscripciones})

def lista_planes(request):
    # público Sportlife — catálogo visible sin login. Gestión de planes (/planes/nuevo/) sí requiere login.
    planes = Plan.objects.all().order_by('precio')
    return render(request, 'Gimnasio/planes.html', {'planes': planes})

@login_required
def lista_socios(request):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    plan_filtro = request.GET.get('plan', 'todos')
    q = request.GET.get('q', '').strip()
    socios = Socio.objects.select_related('plan').all()
    if plan_filtro != 'todos':
        socios = socios.filter(plan__nombre=plan_filtro)
    if q:
        socios = socios.filter(Q(nombre__icontains=q) | Q(rut__icontains=q) | Q(email__icontains=q))
    planes = Plan.objects.all()
    return render(request, 'Gimnasio/socios_list.html', {'socios': socios, 'planes': planes, 'plan_filtro': plan_filtro, 'q': q})

def registro_publico(request):
    # PÚBLICO Sportlife — cualquiera puede inscribirse eligiendo plan + clase, se guardan Socio + Inscripcion. No requiere login.
    plan_id = request.GET.get('plan')
    clase_id = request.GET.get('clase')
    initial = {}
    if plan_id:
        try:
            initial['plan'] = Plan.objects.get(pk=plan_id).pk
        except Plan.DoesNotExist:
            pass
    clases_data = _ocupacion_por_clase()
    clases = Clase.objects.all().order_by('nombre')
    ocup_map = {d['obj'].pk: d['ocupados'] for d in clases_data}
    if request.method == 'POST':
        form = SocioForm(request.POST)
        clase_sel = request.POST.get('clase')
        clase_obj = None
        if clase_sel:
            try:
                clase_obj = Clase.objects.get(pk=clase_sel)
                if Inscripcion.objects.filter(clase=clase_obj, estado='ACTIVA').count() >= clase_obj.capacidad_maxima:
                    form.add_error(None, f'La clase {clase_obj.nombre} está llena ({clase_obj.capacidad_maxima} cupos). Elige otra.')
                    clase_obj = None
            except Clase.DoesNotExist:
                form.add_error(None, 'Clase seleccionada no existe.')
        else:
            form.add_error(None, 'Debes seleccionar una clase.')
        if form.is_valid() and clase_obj:
            socio = form.save()
            Inscripcion.objects.create(socio=socio, clase=clase_obj, estado='ACTIVA')
            messages.success(request, f'¡Bienvenido {socio.nombre}! Te has inscrito en {socio.plan.nombre} + {clase_obj.nombre} — ${socio.plan.precio}. Datos y clase guardados.')
            return redirect('Gimnasio:lista_planes')
    else:
        form = SocioForm(initial=initial)
        if clase_id:
            try:
                Clase.objects.get(pk=clase_id)
            except Clase.DoesNotExist:
                clase_id = None
    return render(request, 'Gimnasio/socio_form.html', {'form': form, 'titulo': 'Inscribirme — Completa tus datos y elige tu clase', 'is_public': True, 'clases': clases, 'clases_data': clases_data, 'ocup_map': ocup_map, 'clase_preseleccionada': clase_id or request.POST.get('clase', '')})

@login_required
def crear_socio(request):
    # ADMIN protegido — solo staff puede registrar desde /socios/nuevo/
    if not request.user.is_staff:
        return redirect('Gimnasio:lista_planes')
    plan_id = request.GET.get('plan')
    clase_id = request.GET.get('clase')
    initial = {}
    if plan_id:
        try:
            initial['plan'] = Plan.objects.get(pk=plan_id).pk
        except Plan.DoesNotExist:
            pass
    clases_data = _ocupacion_por_clase()
    clases = Clase.objects.all().order_by('nombre')
    ocup_map = {d['obj'].pk: d['ocupados'] for d in clases_data}
    if request.method == 'POST':
        form = SocioForm(request.POST)
        clase_sel = request.POST.get('clase')
        # validar clase seleccionada y capacidad antes de crear socio
        clase_obj = None
        if clase_sel:
            try:
                clase_obj = Clase.objects.get(pk=clase_sel)
                if Inscripcion.objects.filter(clase=clase_obj, estado='ACTIVA').count() >= clase_obj.capacidad_maxima:
                    form.add_error(None, f'La clase {clase_obj.nombre} está llena ({clase_obj.capacidad_maxima} cupos). Elige otra.')
                    clase_obj = None
            except Clase.DoesNotExist:
                form.add_error(None, 'Clase seleccionada no existe.')
        else:
            form.add_error(None, 'Debes seleccionar una clase.')
        if form.is_valid() and clase_obj:
            socio = form.save()
            Inscripcion.objects.create(socio=socio, clase=clase_obj, estado='ACTIVA')
            messages.success(request, f'¡Bienvenido {socio.nombre}! Te has inscrito en {socio.plan.nombre} + {clase_obj.nombre} — ${socio.plan.precio}. Datos y clase guardados.')
            if request.user.is_authenticated and request.user.is_staff:
                return redirect('Gimnasio:lista_socios')
            return redirect('Gimnasio:lista_planes')
    else:
        form = SocioForm(initial=initial)
        # preselección clase si viene en URL
        if clase_id:
            try:
                Clase.objects.get(pk=clase_id)
            except Clase.DoesNotExist:
                clase_id = None
    titulo = 'Inscribirme — Completa tus datos y elige tu clase'
    if request.user.is_authenticated and request.user.is_staff:
        titulo = 'Registrar Nuevo Socio'
    return render(request, 'Gimnasio/socio_form.html', {'form': form, 'titulo': titulo, 'is_public': not (request.user.is_authenticated and request.user.is_staff), 'clases': clases, 'clases_data': clases_data, 'ocup_map': ocup_map, 'clase_preseleccionada': clase_id or request.POST.get('clase', '')})

@login_required
def editar_socio(request, pk):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    socio = get_object_or_404(Socio, pk=pk)
    if request.method == 'POST':
        form = SocioForm(request.POST, instance=socio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Socio actualizado.')
            return redirect('Gimnasio:lista_socios')
    else:
        form = SocioForm(instance=socio)
    return render(request, 'Gimnasio/socio_form.html', {'form': form, 'titulo': f'Editar Socio — {socio.nombre}'})

@login_required
def eliminar_socio(request, pk):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    socio = get_object_or_404(Socio, pk=pk)
    if request.method == 'POST':
        socio.delete()
        messages.success(request, 'Socio eliminado. Sus inscripciones (CASCADE) también fueron eliminadas.')
        return redirect('Gimnasio:lista_socios')
    return render(request, 'Gimnasio/confirm_delete.html', {'obj': socio, 'tipo': 'Socio', 'cancel_url': 'Gimnasio:lista_socios'})

@login_required
def detalle_socio(request, pk):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    socio = get_object_or_404(Socio, pk=pk)
    inscripciones = Inscripcion.objects.filter(socio=socio).select_related('clase').order_by('-fecha_inscripcion')
    if request.method == 'POST':
        form = InscripcionForm(request.POST)
        if form.is_valid():
            ins = form.save(commit=False)
            ins.socio = socio
            ins.save()
            messages.success(request, f'Inscripción a {ins.clase.nombre} creada.')
            return redirect('Gimnasio:detalle_socio', pk=socio.pk)
    else:
        form = InscripcionForm(initial={'socio': socio, 'estado': 'ACTIVA'})
        form.fields['socio'].widget = django_forms.HiddenInput()
    return render(request, 'Gimnasio/detalle_socio.html', {'socio': socio, 'inscripciones': inscripciones, 'form': form})

@login_required
def lista_clases(request):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    ocupacion = _ocupacion_por_clase()
    return render(request, 'Gimnasio/clases.html', {'ocupacion': ocupacion})

@login_required
def crear_clase(request):
    if not request.user.is_staff:
        return redirect('Gimnasio:lista_planes')
    if request.method == 'POST':
        form = ClaseForm(request.POST)
        if form.is_valid():
            clase = form.save()
            messages.success(request, f'Clase {clase.nombre} — {clase.instructor} creada.')
            return redirect('Gimnasio:lista_clases')
    else:
        form = ClaseForm()
    return render(request, 'Gimnasio/clase_form.html', {'form': form})

@login_required
def crear_plan(request):
    if not request.user.is_staff:
        return redirect('Gimnasio:lista_planes')
    if request.method == 'POST':
        form = PlanForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, f'Plan {plan.nombre} ${plan.precio}/{plan.duracion_dias}d creado.')
            return redirect('Gimnasio:lista_planes')
    else:
        form = PlanForm()
    return render(request, 'Gimnasio/plan_form.html', {'form': form})

@login_required
def lista_inscripciones(request):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    estado = request.GET.get('estado', 'todos')
    clase_f = request.GET.get('clase', 'todos')
    fecha = request.GET.get('fecha', '')
    qs = Inscripcion.objects.select_related('socio','clase').all().order_by('-fecha_inscripcion')
    if estado != 'todos':
        qs = qs.filter(estado=estado)
    if clase_f != 'todos':
        qs = qs.filter(clase__nombre=clase_f)
    if fecha:
        qs = qs.filter(fecha_inscripcion=fecha)
    clases = Clase.objects.all()
    return render(request, 'Gimnasio/inscripciones.html', {'inscripciones': qs, 'clases': clases, 'estado': estado, 'clase_f': clase_f, 'fecha': fecha})

@login_required
def crear_inscripcion(request):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    if request.method == 'POST':
        form = InscripcionForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inscripción creada.')
            return redirect('Gimnasio:lista_inscripciones')
    else:
        form = InscripcionForm(initial={'estado':'ACTIVA'})
    return render(request, 'Gimnasio/inscripcion_form.html', {'form': form})

@login_required
def cambiar_estado_inscripcion(request, pk, nuevo):
    if not request.user.is_staff:
        return redirect('Gimnasio:cliente_home')
    ins = get_object_or_404(Inscripcion, pk=pk)
    if nuevo in ('ACTIVA','CANCELADA','FINALIZADA'):
        if nuevo == 'ACTIVA':
            ocup = Inscripcion.objects.filter(clase=ins.clase, estado='ACTIVA').exclude(pk=ins.pk).count()
            if ocup >= ins.clase.capacidad_maxima:
                messages.error(request, f'No se puede activar — {ins.clase.nombre} está llena ({ocup}/{ins.clase.capacidad_maxima}).')
                return redirect('Gimnasio:lista_inscripciones')
        ins.estado = nuevo
        ins.save()
        messages.success(request, f'Inscripción #{ins.pk} ahora {nuevo}.')
    return redirect('Gimnasio:lista_inscripciones')
