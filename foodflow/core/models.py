from django.db import models

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
    es_urgente = models.BooleanField(default=False) # NUEVO CAMPO

class DetallePedido(models.Model):
    pedido = models.ForeignKey(Pedido, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField(default=1)
    nota = models.CharField(max_length=200, blank=True, null=True)