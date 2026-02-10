from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, View, ListView
from django.contrib.auth.views import LoginView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import JsonResponse
import json
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import logout
from django.db.models import Sum
from datetime import date
from django.contrib import messages
from django.views.decorators.csrf import csrf_exempt

# Importamos tus modelos
from .models import Mesa, Categoria, Producto, Pedido, DetallePedido, Venta

# --- 1. SEGURIDAD (MIXINS) ---
class SoloCajaMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Caja').exists()

class SoloCocinaMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Cocina').exists()

class SoloMeseroMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_superuser or self.request.user.groups.filter(name='Mesero').exists()

# --- 2. VISTA DE LOGIN ---
class CustomLoginView(LoginView):
    template_name = 'core/login.html'
    redirect_authenticated_user = True

    def get_success_url(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Caja').exists():
            return reverse_lazy('reporte_ventas')
        elif user.groups.filter(name='Cocina').exists():
            return reverse_lazy('cocina')
        elif user.groups.filter(name='Mesero').exists():
            return reverse_lazy('mesero')
        return reverse_lazy('index')

# --- 3. VISTAS PRINCIPALES (FUSIONADAS) ---

# Vista MESERO: Seguridad + Datos de Mesas/Categorías + Template Correcto
class MeseroView(SoloMeseroMixin, ListView):
    template_name = "mesero/mesero.html"
    model = Mesa
    context_object_name = 'mesas'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categorias'] = Categoria.objects.prefetch_related('productos').all()
        
        # --- LÓGICA PARA EL SIGUIENTE ID ---
        ultimo_pedido = Pedido.objects.last()
        if ultimo_pedido:
            siguiente_id = ultimo_pedido.id + 1
        else:
            siguiente_id = 1 # Si es el primer pedido de la historia
            
        context['siguiente_id'] = siguiente_id # Enviamos el dato al HTML
        # -----------------------------------
        
        return context

# Vista COCINA: Seguridad + Datos de Pedidos + Template Correcto
class CocinaView(SoloCocinaMixin, TemplateView):
    template_name = "cocina/cocina.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['pedidos'] = Pedido.objects.filter(
            estado__in=['pendiente', 'preparacion']
        ).order_by('creado_en') # <--- CORREGIDO: Usamos 'creado_en'
        return context

# Vista REPORTES: Seguridad + Datos de Ventas
class ReporteDiarioView(SoloCajaMixin, TemplateView):
    template_name = 'core/reporte_ventas.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        hoy = date.today()
        ventas_hoy = Venta.objects.filter(fecha_venta__date=hoy)
        total_dia = ventas_hoy.aggregate(Sum('total'))['total__sum'] or 0
        
        context['ventas'] = ventas_hoy
        context['total_dia'] = total_dia
        context['fecha'] = hoy
        return context

# --- 4. API (LÓGICA INTERNA PARA JS) ---

# En core/views.py

@method_decorator(csrf_exempt, name='dispatch')
class CrearPedidoView(View):
    def post(self, request):
        try:
            data = json.loads(request.body)
            mesa_id = data.get('mesa_id')
            items = data.get('items')
            nota=data.get('notas', ''),
            urgente=data.get('urgente', False),
            metodo_pago = data.get('metodo_pago', 'efectivo') 
            cliente_cedula=data.get('cliente_cedula', '') 

            mesa = get_object_or_404(Mesa, id=mesa_id)
            
            # 1. Crear Pedido
            pedido = Pedido.objects.create(
                mesa=mesa,
                usuario=request.user 
            )
            
            # 2. Guardar productos y sumar
            total_venta = 0
            for item in items:
                prod = Producto.objects.get(id=item['id'])
                cant = int(item['cantidad'])
                total_venta += prod.precio * cant
                
                DetallePedido.objects.create(pedido=pedido, producto=prod, cantidad=cant)
            
            # 3. GUARDAR VENTA (Aquí suele fallar si falta migración)
            total_con_iva = float(total_venta) * 1.15
            
            Venta.objects.create(
                pedido=pedido,
                total=total_con_iva,
                metodo_pago=metodo_pago
            )

            # 4. Mesa Ocupada
            mesa.estado = 'esperando'
            mesa.save()

            return JsonResponse({'status': 'ok'})

        except Exception as e:
            # Esto imprimirá el error real en tu pantalla negra (terminal)
            print(f"❌ ERROR AL CREAR PEDIDO: {str(e)}")
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@method_decorator(csrf_exempt, name='dispatch')
class ActualizarEstadoPedido(View):
    def post(self, request, pk):
        pedido = get_object_or_404(Pedido, pk=pk)
        pedido.estado = 'listo'
        pedido.save()
        
        mesa = pedido.mesa
        mesa.estado = 'lista'
        mesa.save()
        
        return JsonResponse({'status': 'updated'})

# --- 5. LOGOUT Y OTROS ---

def exit_view(request):
    logout(request)
    return redirect('login')

# Vista para procesar el pago (Requerida para el botón de Caja)
def procesar_pago(request, mesa_id):
    from django.contrib import messages
    mesa = get_object_or_404(Mesa, id=mesa_id)
    pedido = Pedido.objects.filter(mesa=mesa).exclude(estado='pagado').last()
    
    if pedido:
        Venta.objects.create(pedido=pedido, total=pedido.total_pedido)
        pedido.estado = 'pagado'
        pedido.save()
        mesa.estado = 'libre'
        mesa.save()
        messages.success(request, f"Pago registrado. Mesa {mesa.numero} liberada.")
    else:
        messages.error(request, "No hay pedidos pendientes.")
    
    return redirect('reporte_ventas') 


def procesar_pago(request, mesa_id):
    mesa = get_object_or_404(Mesa, id=mesa_id)
    # Buscamos el último pedido de esta mesa
    pedido = Pedido.objects.filter(mesa=mesa).last()
    
    if pedido:
        # VERIFICACIÓN INTELIGENTE:
        # Si ya existe una venta para este pedido (porque pagó al inicio), solo liberamos mesa.
        if Venta.objects.filter(pedido=pedido).exists():
             mesa.estado = 'libre'
             mesa.save()
             # Opcional: Marcar pedido como finalizado del todo si tienes ese estado
             pedido.estado = 'pagado'
             pedido.save()
             messages.success(request, f"Mesa {mesa.numero} liberada correctamente.")
        
        else:
            # Si NO existe venta (flujo antiguo), entonces cobramos aquí
            Venta.objects.create(pedido=pedido, total=pedido.total_pedido, metodo_pago='efectivo')
            pedido.estado = 'pagado'
            pedido.save()
            mesa.estado = 'libre'
            mesa.save()
            messages.success(request, "Cobro registrado y mesa liberada.")
            
    return redirect('mesero') # Regresamos al mapa de mesas

@csrf_exempt
def reportar_problema(request, pk):
    if request.method == 'POST':
        try:
            pedido = Pedido.objects.get(pk=pk)
            # Puedes usar un estado nuevo o simplemente cambiar la nota
            pedido.estado = 'problema' # Asegúrate de que tu modelo soporte este estado o usa 'pendiente'
            pedido.save()
            return JsonResponse({'status': 'ok'})
        except Pedido.DoesNotExist:
            return JsonResponse({'status': 'error', 'msg': 'Pedido no encontrado'}, status=404)