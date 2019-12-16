USUARIO_GRUP = {
    'USURAIO_I': 'Super Admin',
    'USUARIO_II': 'Admin',
    'USUARIO_III': 'Usuario'
}

FORMA_DE_PAGO = (
	(1,'Contado'),
	(2,'Credito'),
	(3,'Sin costo')
)

TIPO_DOCUMENTO = (
  (33, 'Factura electrónica'),
  (39, 'Boleta electrónica'),
  (52, 'Guía de despacho electrónica'),
  (56, 'Nota de débito electrónica'),
  (61, 'Nota de crédito electrónica'),
)

VALOR_DESCUENTO = (
  ('%','%'),
  ('$','$')
)

CODIGO_REFERENCIA = (
  (1,'Anula Documento'),
  (2,'Corrige Texto del Documento'),
  (3,'Corrige Montos')
)

documentos_dict = dict((key, value) for key, value in TIPO_DOCUMENTO)