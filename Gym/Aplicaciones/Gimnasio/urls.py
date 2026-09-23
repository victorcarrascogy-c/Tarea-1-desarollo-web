from django.urls import path
from . import views

app_name = 'Gimnasio'

urlpatterns = [
    # Login separado
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # Cliente (solo pagar su plan)
    path('cliente/', views.cliente_home, name='cliente_home'),
    path('cliente/pagar/', views.cliente_pagar, name='cliente_pagar'),
    path('cliente/inscribir/', views.cliente_inscribir, name='cliente_inscribir'),
    # Admin
    path('', views.home, name='home'),
    path('prototipo/', views.prototipo, name='prototipo'),
    path('planes/', views.lista_planes, name='lista_planes'),
    path('registro/', views.registro_publico, name='registro'),
    path('socios/', views.lista_socios, name='lista_socios'),
    path('socios/nuevo/', views.crear_socio, name='crear_socio'),
    path('socios/<int:pk>/editar/', views.editar_socio, name='editar_socio'),
    path('socios/<int:pk>/eliminar/', views.eliminar_socio, name='eliminar_socio'),
    path('socios/<int:pk>/', views.detalle_socio, name='detalle_socio'),
    path('clases/', views.lista_clases, name='lista_clases'),
    path('clases/nueva/', views.crear_clase, name='crear_clase'),
    path('planes/nuevo/', views.crear_plan, name='crear_plan'),
    path('inscripciones/', views.lista_inscripciones, name='lista_inscripciones'),
    path('inscripciones/nueva/', views.crear_inscripcion, name='crear_inscripcion'),
    path('inscripciones/<int:pk>/estado/<str:nuevo>/', views.cambiar_estado_inscripcion, name='cambiar_estado'),
]
