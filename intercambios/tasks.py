"""!
Controlador para el manejo de tareas de modulo intercambio

@author Rodrigo A. Boet (rudmanmrrod at gmail.com)
@date 15-07-2019
@version 1.0.0
"""

import imaplib, email, os

from datetime import datetime

from django.conf import settings
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import RedirectView

from celery import shared_task
from celery.decorators import task
from celery.utils.log import get_task_logger

from conectores.models import Compania

from .models import (
    Intercambio, DteIntercambio
)
from utils.views import DecodeEncodeChain

logger = get_task_logger(__name__)


class RefrescarBandejaRedirectView(RedirectView):
  """
  Clase para refrescar la bandeja de entrada
  @author Alberto Rincones (alberto at timg.cl)
  @copyright TIMG
  @date 05-04-19 (dd-mm-YY)
  @version 1.0
  """

  def get_redirect_url(self, *args, **kwargs):
    pk=self.kwargs.get('pk')

    updateInbox.apply_async(args=[pk], countdown=1)

    return reverse_lazy('intercambios:lista', kwargs={'pk':pk})

  def search(self, key, value, con):

    result, data = con.search(None,key,'"{}"'.format(value))
    return data

  def get_emails(self,results_bytes, mail):

    msgs = []
    for num in results_bytes[0].split():

      type, data = mail.fetch(num, "(RFC822)")
      msgs.append(data)
    return msgs

  def get_body(self, msg):

    if msg.is_multipart():
      return self.get_body(msg.get_payload(0))
    else:
      return msg.get_payload(None, True)

  def get_attachment(self, msg):

    attachment_count = 0
    attachment_dict = dict() 
    for part in msg.walk():
      if part.get_content_maintype() == 'multipart':
        continue
      if part.get('Content-Disposition') is None:
        continue
      attachment_count += 1
      fileName = part.get_filename()
      if fileName is not None:
        decoded_filename = str(email.header.make_header(email.header.decode_header(fileName)))
        attachment_dict[decoded_filename] = part.get_payload(decode=True)
      else:
        attachment_dict["dte"+str(attachment_count)] = part.get_payload(decode=True)
    return (attachment_count,attachment_dict)

  def get_received_time(self, received_string):

    list_ = received_string.split('\r\n')
    final_date = list_[0].split(';')[1].strip()
    if(final_date==''):
      final_date = list_[1].strip()
    other_date = " ".join(final_date.split(" ")[:-2])
    #string_date = "{} {} {}".format(final_date[2], final_date[1], final_date[3])
    datef = datetime.strptime(str(other_date.strip()), '%a, %d %b %Y %H:%M:%S')
    datef.replace(tzinfo=timezone.utc)
    return datef


  def get_remisor(self, remisor_string):

    remisor = remisor_string.split('<')
    if len(remisor) > 1: 
      remisor_mail = remisor[1].strip('<>')
      remisor_name = remisor[0].strip()
      return remisor_name, remisor_mail
    else:
      return "Desconocido", remisor[0]

def sycnInbox(comp, mail, refresh):
    """
    """
    last_email = 0
    local_last_email_code = last_email
    decode_encode = DecodeEncodeChain()
    assert comp.correo_intercambio, "No hay correo"
    assert comp.pass_correo_intercambio, "No hay password"
    correo = comp.correo_intercambio.strip()
    passw = comp.pass_correo_intercambio.strip()
    passw = decode_encode.decrypt(passw).decode("utf-8")
    try:
      mail.login(correo,passw)
    except imaplib.IMAP4.error as e:
        logger.warning("Hubo un error al conectarse al correo: {0} error: {1}".format(correo, e))
        pass

    mail.list()
    mail.select("inbox")
    result, data = mail.search(None, "ALL")
    id_list = data[0].split()
    
    if len(id_list) >= 1:
        last_email_code = int(id_list[-1].decode())
    else:
        last_email_code = 0

    if last_email_code > local_last_email_code:
      new_elements = last_email_code - local_last_email_code
    else:
      logger.warning("No posee nuevos correos")
      return False

    if new_elements == 1:
      latest_emails = [id_list[-1]]
    else:
      latest_emails = id_list[-new_elements:]

    #latest_emails = latest_emails[0:50]
    
    for element in latest_emails:
      result, email_data = mail.fetch(element, "(RFC822)")
      raw_email = email_data[0][1]
      raw_multipart = email.message_from_bytes(raw_email)

      try:
        raw_email_string = raw_email.decode('utf-8')
      except Exception as e:
        raw_email_string = raw_email.decode('latin-1')

      email_message = email.message_from_string(raw_email_string)
      attachment_count, attachments = refresh.get_attachment(raw_multipart)
      
      remisor_name, remisor_email = refresh.get_remisor(str(email.header.make_header(email.header.decode_header(email_message['From']))))
      
      try:
        date = refresh.get_received_time(str(email.header.make_header(email.header.decode_header(email_message['Received']))))
      except:
        date = None
        pass

      try:
        titulo = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
      except:
        titulo = "No se pudo obtener el titulo"
        pass

      obj, created = Intercambio.objects.update_or_create(
        #codigo_email = element.decode(),
        receptor=comp,
        email_remisor=remisor_email,
        fecha_de_recepcion=date,
        defaults={
                "remisor" : remisor_name,
                "cantidad_dte" : attachment_count,
                "titulo" : titulo,
                "contenido" : str(refresh.get_body(raw_multipart).decode('latin-1'))}
      )
      if attachment_count > 0:
        for attach in attachments:
          filename = attach

          download_folder = obj.receptor.rut

          initial_route = os.path.join(settings.MEDIA_ROOT, 'intercambio_dte') 
          if not os.path.isdir(initial_route):
            os.mkdir(initial_route)
          
          relative_path =  os.path.join(initial_route, download_folder)

          if not os.path.isdir(relative_path):
            os.mkdir(relative_path)

          att_path = os.path.join(filename)
          fp = open(os.path.join(initial_route, relative_path, att_path), 'wb')
          fp.write(attachments[attach])
          fp.close()

          fp = open(os.path.join(initial_route, relative_path, att_path), 'rb')          
          attach_dte = DteIntercambio(id_intercambio=obj)
          
          attach_dte.dte_attachment.save(att_path, fp) 
        
          fp.close()
      if comp.borrar_correo_intercambio:
        mail.store(element, '+FLAGS', r'(\Deleted)')  
    logger.info("Cantidad de correos nuevos: {}".format(new_elements))


@shared_task
def updateInbox(compania=None):
    """
    Funcion que permite ejecutar una tarea para actualizar los correos de la bandeja de entrada automaticamente.

    @author Rodrigo A. Boet (rudmanmrrod at gmail.com)
    @date 15-07-2019
    @version 1.0.0
    @return True o False
    """
    refresh = RefrescarBandejaRedirectView()

    try:
        obj_compania = Compania.objects.get(pk=compania) if compania else Compania.objects.all()  
    except Exception as e:
        print(e)
    try:
        iter(obj_compania)
        num_compania = len(obj_compania)
    except Exception as e:
        num_compania = 0

    mail = imaplib.IMAP4_SSL(obj_compania.imap_correo_intercambio)
    
    if num_compania > 0:
        for comp in obj_compania:
            sycnInbox(comp, mail, refresh)
        return True
    else:
        sycnInbox(obj_compania, mail, refresh)
        return True
        