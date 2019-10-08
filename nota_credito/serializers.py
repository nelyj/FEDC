from django.db import transaction
import json
from rest_framework import serializers
from conectores.models import Compania
from .models import notaCredito

class ProductSerializer(serializers.Serializer):
  """!
  Serializer de Producto

  @author Rodrigo Boet (rudmanmrrod at gmail.com)
  @date 08-10-2019
  @version 1.0.0
  """
  codigo = serializers.CharField(max_length=50)
  nombre = serializers.CharField(max_length=150)
  cantidad = serializers.IntegerField(min_value=1)
  precio = serializers.DecimalField(10,5)

class notaCreditoSerializer(serializers.ModelSerializer):
  """!
  Serializer de Nota de Credito

  @author Rodrigo Boet (rudmanmrrod at gmail.com)
  @date 08-10-2019
  @version 1.0.0
  """
  class Meta:
    model = notaCredito
    exclude = ('monto_palabra','direccion')
    extra_kwargs = {
      'compania': {'required': True},
      'numero_factura': {'required': True},
      'senores': {'required': True},
      'comuna': {'required': True},
      'region': {'required': True},
      'ciudad_receptora': {'required': True},
      'giro': {'required': True},
      'rut': {'required': True},
      'fecha': {'required': True},
      'productos': {'required': True},
    } 

  def validate(self, attrs):
    """
    Método para validar el serializer

    @param attrs objeto con los atributos
    @return Retorna los atributos validados
    """
    compania = attrs.get('compania')
    productos = attrs.get('productos')
    fecha = attrs.get('fecha')
    # Se valida que el usuario pertenezca a la compañia
    if(compania.owner_id != self.context['request'].user.id):
      msg = "El usuario no pertenece a está compañia"
      raise serializers.ValidationError(msg)
    # Se valida la fecha
    datetime_object = datetime.datetime.now()
    if fecha > datetime_object:
      msg = "La fecha no puede ser mayor a la fecha actual, por favor verifica nuevamente la fecha"
      raise serializers.ValidationError(msg)
    # Se verifica el folio
    try:
      folio = Folio.objects.filter(empresa=compania.pk,is_active=True,vencido=False,tipo_de_documento=33).order_by('fecha_de_autorizacion').first()
      if not folio:
        raise Folio.DoesNotExist
    except Folio.DoesNotExist:  
      msg = "No posee folios para asignacion de timbre"
      raise serializers.ValidationError(msg)
    try:
      folio.verificar_vencimiento()
    except ElCAFSenEncuentraVencido:
      msg = "El CAF se encuentra vencido"
      raise serializers.ValidationError(msg)
    #try:
    #  self.object.recibir_folio(folio)
    #except (ElCafNoTieneMasTimbres, ValueError):
    #  msg = "Ya ha consumido todos sus timbres"
    #  raise serializers.ValidationError(msg)

    # Se valida el producto
    try:
      productos = json.loads(productos)
      for producto in productos:
        keys = producto.keys()
        if('nombre' not in keys or 'codigo' not in keys or\
          'cantidad' not in keys or 'precio' not in keys):
          msg = "La estructura del producto no es correcta"
          raise serializers.ValidationError(msg)
        if(type(producto['nombre'])!=str or type(producto['codigo'])!=str):
          msg = "El nombre y el código del producto deben ser carácteres"
          raise serializers.ValidationError(msg)
        if(type(producto['cantidad'])!=int):
          msg = "La cantidad del producto debe ser entero"
          raise serializers.ValidationError(msg)
        if(type(producto['precio'])!=int and type(producto['precio'])!=float):
          msg = "El precio del producto debe ser númerico"
          raise serializers.ValidationError(msg)
    except Exception as e:
      print(e)
      raise e
    #password = attrs.get('password')

    """if username and password:
    user = User.objects.filter(
    Q(username__iexact=username)|
    Q(email__iexact=username)
    ).distinct()

    if user:
    user = user.first()
    if user.check_password(password):
    if not user.is_active:
    msg = _('User not active!')
    raise serializers.ValidationError(msg)
    else:
    msg = _('Invalid the password!')
    raise serializers.ValidationError(msg)
    else:
    raise serializers.ValidationError(_('Invalid credentials!'))
    else:
    msg = _('Must include "username" and "password".')
    raise serializers.ValidationError(msg)

    attrs['user'] = user"""
    return attrs

  def create(self, validated_data):
    with transaction.atomic():
      message = notaCredito.objects.create(**validated_data)
      
    return message