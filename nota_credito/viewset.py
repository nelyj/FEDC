from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from conectores.models import Compania
from .models import notaCredito
from .serializers import notaCreditoSerializer

class NotaCreditoViewSet(viewsets.ModelViewSet):
  """!
    Viewset de nota de cŕedito
    @author Rodrigo Boet (rudmanmrrod at gmail)
    @date 08-10-2019
  """
  serializer_class = notaCreditoSerializer
  #filter_fields = ('chat_type','chat_user_chat__user_id')

  def get_queryset(self):
    """
    Método para crea la nota de cŕedito

    @param self Objeto de instancia del método
    @param request Objeto de la petición
    @return Retorna la data creada
    """
    companias = Compania.objects.filter(owner_id=self.request.user.id).values_list('id',flat=True)
    return notaCredito.objects.filter(compania__in=companias)

  def create(self, request, format = None):
    """
    Método para crea la nota de cŕedito

    @param self Objeto de instancia del método
    @param request Objeto de la petición
    @return Retorna la data creada
    """
    serializer = self.get_serializer(data=request.data,context={'request': request})
    serializer.is_valid(raise_exception=True)
    serializer.save() 
    return Response(serializer.data, status=status.HTTP_201_CREATED)