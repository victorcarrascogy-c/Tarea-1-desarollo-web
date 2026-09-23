from django.contrib import admin
from .models import Plan, Socio, Clase, Inscripcion


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'precio', 'duracion_dias', 'costo_diario_display')
    list_filter = ('duracion_dias',)
    search_fields = ('nombre',)
    ordering = ('precio',)

    @admin.display(description='Costo diario')
    def costo_diario_display(self, obj):
        return f"${obj.costo_diario()}"


@admin.register(Socio)
class SocioAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rut', 'email', 'plan')
    list_filter = ('plan',)
    search_fields = ('nombre', 'rut', 'email')
    ordering = ('nombre',)
    list_select_related = ('plan',)


@admin.register(Clase)
class ClaseAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'instructor', 'capacidad_maxima')
    list_filter = ('instructor',)
    search_fields = ('nombre', 'instructor')
    ordering = ('nombre',)


@admin.register(Inscripcion)
class InscripcionAdmin(admin.ModelAdmin):
    list_display = ('id', 'socio', 'clase', 'estado', 'fecha_inscripcion')
    list_filter = ('estado', 'fecha_inscripcion', 'clase')
    search_fields = ('socio__nombre', 'socio__rut', 'clase__nombre')
    ordering = ('-fecha_inscripcion',)
    list_select_related = ('socio', 'clase')
    date_hierarchy = 'fecha_inscripcion'
    autocomplete_fields = ('socio', 'clase')
