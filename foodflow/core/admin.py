from django.contrib import admin
from .models import Mesa, Categoria, Producto, Pedido, DetallePedido, Venta

# Configuración para Productos
class ProductoAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'categoria', 'precio', 'activo')
    list_filter = ('categoria',)

# Esto permite ver los platos dentro del pedido
class DetalleInline(admin.TabularInline):
    model = DetallePedido
    extra = 0

# Configuración UNIFICADA para Pedidos
class PedidoAdmin(admin.ModelAdmin):
    # Columnas que se ven en la lista (incluida la cédula)
    list_display = ('id', 'mesa', 'cliente_cedula', 'metodo_pago', 'total', 'estado', 'creado_en')
    
    # Filtros laterales
    list_filter = ('estado', 'creado_en', 'metodo_pago')
    
    # Barra de búsqueda (puedes buscar por ID o por Cédula)
    search_fields = ('cliente_cedula', 'id')
    
    # Platos dentro del pedido
    inlines = [DetalleInline]

# Configuración para Ventas
class VentaAdmin(admin.ModelAdmin):
    list_display = ('id', 'pedido', 'total', 'metodo_pago', 'fecha_venta')
    list_filter = ('fecha_venta', 'metodo_pago')

# --- REGISTROS FINALES (Solo una vez cada uno) ---
admin.site.register(Mesa)
admin.site.register(Categoria)
admin.site.register(Producto, ProductoAdmin)
admin.site.register(Pedido, PedidoAdmin) # Aquí registramos el pedido con su admin
admin.site.register(Venta, VentaAdmin)