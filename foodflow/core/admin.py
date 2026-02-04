from django.contrib import admin
from .models import Mesa, Categoria, Producto, Pedido, DetallePedido

# Configuración bonita para el admin
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'activo')
    list_filter = ('categoria',)

class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

class PedidoAdmin(admin.ModelAdmin):
    list_display = ('id', 'mesa', 'estado', 'creado_en')
    list_filter = ('estado',)
    inlines = [DetalleInline]

admin.site.register(Mesa)
admin.site.register(Categoria)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Pedido, PedidoAdmin)