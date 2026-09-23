import re
from django import forms
from .models import Socio, Inscripcion, Plan, Clase

class SocioForm(forms.ModelForm):
    class Meta:
        model = Socio
        fields = ['nombre', 'rut', 'email', 'plan']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Juan Pérez'}),
            'rut': forms.TextInput(attrs={'class': 'input', 'placeholder': '12.345.678-9'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'juan@mail.cl'}),
            'plan': forms.Select(attrs={'class': 'input'}),
        }
        labels = {
            'nombre': 'Nombre completo',
            'rut': 'RUT',
            'email': 'Correo electrónico',
            'plan': 'Plan contratado',
        }

    def clean_rut(self):
        rut = self.cleaned_data['rut'].strip()
        # formato básico chileno: 7-8 dígitos + guión + dígito/k
        if not re.match(r'^\d{7,8}-[\dkK]$', rut.replace('.', '')):
            # permitir con puntos también
            clean = rut.replace('.', '')
            if not re.match(r'^\d{7,8}-[\dkK]$', clean):
                raise forms.ValidationError('Formato de RUT no válido. Ej: 12.345.678-9')
        # normalizar: mantener como ingresado pero validar duplicado lo hace unique
        qs = Socio.objects.filter(rut=rut)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError('Formato de RUT o duplicado no permitido — ya existe un socio con ese RUT.')
        return rut


class PlanForm(forms.ModelForm):
    class Meta:
        model = Plan
        fields = ['nombre', 'precio', 'duracion_dias']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Quincenal'}),
            'precio': forms.NumberInput(attrs={'class': 'input', 'placeholder': '18000', 'min': '0'}),
            'duracion_dias': forms.NumberInput(attrs={'class': 'input', 'placeholder': '15', 'min': '1'}),
        }
        labels = {
            'nombre': 'Nombre del plan',
            'precio': 'Precio ($)',
            'duracion_dias': 'Duración (días)',
        }

class ClaseForm(forms.ModelForm):
    class Meta:
        model = Clase
        fields = ['nombre', 'instructor', 'capacidad_maxima']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Spinning'}),
            'instructor': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Ej: Laura Díaz'}),
            'capacidad_maxima': forms.NumberInput(attrs={'class': 'input', 'placeholder': '20', 'min': '1'}),
        }
        labels = {
            'nombre': 'Nombre de la clase',
            'instructor': 'Instructor',
            'capacidad_maxima': 'Capacidad máxima',
        }

class InscripcionForm(forms.ModelForm):
    class Meta:
        model = Inscripcion
        fields = ['socio', 'clase', 'estado']
        widgets = {
            'socio': forms.Select(attrs={'class': 'input'}),
            'clase': forms.Select(attrs={'class': 'input'}),
            'estado': forms.Select(attrs={'class': 'input'}),
        }

    def clean(self):
        cleaned = super().clean()
        clase = cleaned.get('clase')
        # verificar capacidad solo si estado ACTIVA
        estado = cleaned.get('estado') or 'ACTIVA'
        if clase and estado == 'ACTIVA':
            # contar inscripciones activas para esa clase
            qs = Inscripcion.objects.filter(clase=clase, estado='ACTIVA')
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            ocupados = qs.count()
            if ocupados >= clase.capacidad_maxima:
                raise forms.ValidationError(f'Capacidad máxima alcanzada — {clase.nombre} está llena ({ocupados}/{clase.capacidad_maxima}).')
        return cleaned
