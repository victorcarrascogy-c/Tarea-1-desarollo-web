from django.db import models

class Plan(models.Model):
    nombre = models.CharField(max_length=50)
    precio = models.IntegerField()
    duracion_dias = models.IntegerField(default=30)

    class Meta:
        ordering = ['precio']

    def __str__(self):
        return f"Plan {self.nombre} (${self.precio})"

    # Regla de negocio en el modelo: calcula el costo diario del plan
    def costo_diario(self):
        return round(self.precio / self.duracion_dias)


class Socio(models.Model):
    nombre = models.CharField(max_length=100)
    rut = models.CharField(max_length=12, unique=True)
    email = models.EmailField()
    # PROTECT: No se puede borrar un Plan si existen socios matriculados en él
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"{self.nombre} ({self.rut})"


class Clase(models.Model):
    nombre = models.CharField(max_length=50) # ej: "Spinning", "CrossFit", "Yog
    instructor = models.CharField(max_length=100)
    capacidad_maxima = models.IntegerField()

    class Meta:
        ordering = ['nombre']

    def __str__(self):
        return f"Clase de {self.nombre} - Prof. {self.instructor}"


class Inscripcion(models.Model):
    ESTADOS = [
        ('ACTIVA', 'Activa'),
        ('CANCELADA', 'Cancelada'),
        ('FINALIZADA', 'Finalizada'),
    ]

    fecha_inscripcion = models.DateField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='ACTIVA')
    # CASCADE: Si se elimina el socio, se eliminan sus inscripciones a clases
    socio = models.ForeignKey(Socio, on_delete=models.CASCADE)
    # PROTECT: No se puede borrar una clase si tiene inscripciones registradas
    clase = models.ForeignKey(Clase, on_delete=models.PROTECT)

    class Meta:
        ordering = ['-fecha_inscripcion']

    def __str__(self):
        return f"Inscripción: {self.socio.nombre} en {self.clase.nombre}"