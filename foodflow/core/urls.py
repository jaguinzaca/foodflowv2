from django.urls import path
# Importación obligatoria para que funcione el logout
from django.contrib.auth.views import LogoutView 
from .views import *

urlpatterns = [
    # Rutas de Acceso
    path('', CustomLoginView.as_view(), name='index'),
    path('login/', CustomLoginView.as_view(), name='login'),
    
    # --- ESTA ES LA LÍNEA CLAVE ---
    path('logout/', exit_view, name='logout'),
    # ------------------------------
    
    path('mesero/', MeseroView.as_view(), name='mesero'),
    path('cocina/', CocinaView.as_view(), name='cocina'),
    path('api/crear_pedido/', CrearPedidoView.as_view(), name='crear_pedido'),
    path('api/pedido/<int:pk>/listo/', ActualizarEstadoPedido.as_view(), name='marcar_listo'),
]