from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User


class Mesa(models.Model):
    ESTADOS = [
        ('libre', 'Libre'),
        ('ocupada', 'Ocupada'),
        ('esperando', 'Esperando Comida'),
        ('lista', 'Comida Lista'), # NUEVO ESTADO
        ('pagar', 'Por Pagar'),
    ]
    numero = models.IntegerField(unique=True)
    estado = models.CharField(max_length=20, choices=ESTADOS, default='libre')

    def __str__(self):
        return f"Mesa {self.numero}"

class Categoria(models.Model):
    nombre = models.CharField(max_length=50)
    def __str__(self): return self.nombre

class Producto(models.Model):
    nombre = models.CharField(max_length=100)
    precio = models.DecimalField(max_digits=6, decimal_places=2)
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='productos')
    activo = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True, null=True)
    
    # --- CAMBIO IMPORTANTE: Usamos ImageField ---
    # upload_to='productos/' creará una carpeta automática para organizar las fotos
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)
    # --------------------------------------------

    def __str__(self):
        return f"{self.nombre} (${self.precio})"
    
class Pedido(models.Model):
    ESTADOS_PEDIDO = [
        ('pendiente', 'Pendiente'),
        ('listo', 'Listo'),
    ]
    mesa = models.ForeignKey(Mesa, on_delete=models.CASCADE)
    creado_en = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=20, choices=ESTADOS_PEDIDO, default='pendiente')
    nota_general = models.TextField(blank=True, null=True)
    es_urgente = models.BooleanField(default=False) 
    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    cliente_cedula = models.CharField(max_length=13, blank=True, null=True, verbose_name="Cédula Cliente")
    metodo_pago = models.CharField(max_length=20, default='efectivo')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)

    @property
    def total_pedido(self):
        # Esta función suma todos los detalles del pedido automáticamente
        total = sum(item.producto.precio * item.cantidad for item in self.detalles.all())
        return total

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    nota = models.CharField(max_length=200, blank=True, null=True)

class Venta(models.Model):
    pedido = models.OneToOneField(Pedido, on_delete=models.CASCADE)
    fecha_venta = models.DateTimeField(default=timezone.now)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    # AGREGA ESTE CAMPO NUEVO:
    metodo_pago = models.CharField(max_length=50, default='efectivo') 
    
    def __str__(self):
        return f"Venta #{self.id} - {self.total}"
    