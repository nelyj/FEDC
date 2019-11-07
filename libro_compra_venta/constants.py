TIPO_OPERACION = [
  "COMPRA",
  "VENTA"
]

TIPO_LIBRO = [
  "MENSUAL", # Si es el libro correspondiente al mensual
  "ESPECIAL", # Si es un fragmento po pedazo en especifico
  "RECTIFICA" # Si es un libro para rectificar
]

TIPO_ENVIO = [
  "PARCIAL", #Indica que es un Envio Parcial del Libro y que Faltan Otros para Completar el Libro
  "FINAL", #Indica que es el Ultimo Envio Parcial. Con Esto se Completa el Libro.
  "TOTAL", #Indica que es el Unico Envio que Compone el Libro
  "AJUSTE", #Indica que es un Envio con Informacion para Corregir un Libro Previamente Enviado
]

CHOICE_LIBRO = (
        (0, TIPO_OPERACION[0]),
        (1, TIPO_OPERACION[1]),
    )

dict_tipo_libro = dict((key, value) for key, value in CHOICE_LIBRO)
