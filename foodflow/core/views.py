from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import TemplateView, View
# Importaciones para el Login
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin
# Importaciones para la API y JSON
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
# Importamos tus modelos
from .models import Mesa, Categoria, Producto, Pedido, DetallePedido
from django.contrib.auth import logout

# --- 1. VISTA DE LOGIN (La que faltaba) ---
class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True # Si ya está logueado, lo manda directo adentro

# --- 2. VISTAS PRINCIPALES ---

class MeseroView(LoginRequiredMixin, TemplateView):
    template_name = "mesero/mesero.html"
    login_url = 'login'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Traemos datos reales de la BD
        context['mesas'] = Mesa.objects.all().order_by('numero')
        context['categorias'] = Categoria.objects.prefetch_related('productos').all()
        return context

class CocinaView(LoginRequiredMixin, TemplateView):
    template_name = "cocina/cocina.html"
    login_url = 'login'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Traemos solo pedidos pendientes o en preparación
        context['pedidos'] = Pedido.objects.filter(
            estado__in=['pendiente', 'preparacion']
        ).order_by('creado_en')
        return context

# --- 3. API (LÓGICA INTERNA PARA JS) ---

@method_decorator(csrf_exempt, name='dispatch')
class CrearPedidoView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            mesa_id = data.get('mesa_id')
            items = data.get('items') # Lista de {id, cantidad, nota}
            notas_grales = data.get('notas')

            mesa = get_object_or_404(Mesa, id=mesa_id)
            
            # Crear el Pedido padre
            pedido = Pedido.objects.create(mesa=mesa, nota_general=notas_grales)
            
            # Crear los detalles (hamburguesas, colas, etc.)
            for item in items:
                producto = Producto.objects.get(id=item['id'])
                DetallePedido.objects.create(
                    pedido=pedido,
                    producto=producto,
                    cantidad=item['cantidad'],
                    nota=item.get('nota', '')
                )
            
            # Cambiar estado de la mesa visualmente
            mesa.estado = 'esperando'
            mesa.save()

            return JsonResponse({'status': 'ok', 'id_pedido': pedido.id})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ActualizarEstadoPedido(View):
    def post(self, request, pk):
        # 1. Buscamos el pedido y lo marcamos listo
        pedido = get_object_or_404(Pedido, pk=pk)
        pedido.estado = 'listo'
        pedido.save()
        
        # 2. AQUÍ ESTABA EL ERROR: Faltaba avisar a la mesa
        mesa = pedido.mesa
        mesa.estado = 'lista'  # Esto activa el color AZUL
        mesa.save()
        
        return JsonResponse({'status': 'updated'})
    
def exit_view(request):
    logout(request)
    return redirect('login')