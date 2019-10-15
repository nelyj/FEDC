"""!
Controlador para el manejo de tareas de modulo intercambio

@author Rodrigo A. Boet (rodrigo.b at timgla.com)
@date 15-07-2019
@version 1.0.0
"""

import imaplib

from celery import shared_task
#from celery.decorators import task

from conectores.models import Compania

from .models import (
    Intercambio, DteIntercambio
)

from .views.RefrescarBandejaRedirectView import (
    get_attachment, get_remisor,
    get_received_time, get_body 
)

logger = get_task_logger(__name__)


# @task(name="update_inbox")

@shared_task
def updateInbox():
    """
    Funcion que permite ejecutar una tarea para actualizar los correos de la bandeja de entrada.

    @author Rodrigo A. Boet (rodrigo.b at timgla.com)
    @date 15-07-2019
    @version 1.0.0
    @return True o False
    """
    compania = None
    mail = imaplib.IMAP4_SSL('imap.gmail.com')

    try:
        obj_compania = Compania.objects.get(pk=compania) if compania else Compania.objects.all()  
    except Exception as e:
        print(e)
    try:
        iter(obj_compania)
        num_compania = len(obj_compania)
    except Exception as e:
        num_compania = 0

    last_email = 0
    if num_compania > 0:
        for comp in obj_compania:
            assert comp.correo_intercambio, "No hay correo"
            assert comp.pass_correo_intercambio, "No hay password"
            correo = comp.correo_intercambio.strip()
            passw = comp.pass_correo_intercambio.strip()
            try:
              mail.login(correo,passw)
            except imaplib.IMAP4.error as e:
                logger.warning("Hubo un error al conectarse al correo: {0} error: {1}".format(correo, e))
                pass

            mail.list()
            mail.select("inbox")
            result, data = mail.search(None, "ALL")
            id_list = data[0].split()

            last_email_code = int(id_list[-1].decode())

            if last_email_code > local_last_email_code:
              new_elements = last_email_code - local_last_email_code
            else:
              logger.warning("No posee nuevos correos")
              pass

            if new_elements == 1:
              latest_emails = [id_list[-1]]
            else:
              latest_emails = id_list[-new_elements:]

            latest_emails = latest_emails[0:5]
            
            for element in latest_emails:
              result, email_data = mail.fetch(element, "(RFC822)")
              raw_email = email_data[0][1]
              raw_multipart = email.message_from_bytes(raw_email)

              try:
                raw_email_string = raw_email.decode('utf-8')
              except Exception as e:
                raw_email_string = raw_email.decode('latin-1')

              email_message = email.message_from_string(raw_email_string)
              attachment_count, attachments = get_attachment(raw_multipart)
              
              remisor_name, remisor_email = get_remisor(str(email.header.make_header(email.header.decode_header(email_message['From']))))
              obj, created = Intercambio.objects.update_or_create(
                #codigo_email = element.decode(),
                receptor=compania,
                email_remisor=remisor_email,
                fecha_de_recepcion=get_received_time(str(email.header.make_header(email.header.decode_header(email_message['Received'])))),
                defaults={
                        "remisor" : remisor_name,
                        "cantidad_dte" : attachment_count,
                        "titulo" : str(email.header.make_header(email.header.decode_header(email_message['Subject']))),
                        "contenido" : str(get_body(raw_multipart).decode('latin-1'))}
              )
              mail.store(element, '+FLAGS', r'(\Deleted)')
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
                  
            logger.info("Cantidad de correos nuevos: {}".format(new_elements))

        return True
