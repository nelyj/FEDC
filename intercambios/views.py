import imaplib, email, os, json
from base64 import b64decode,b64encode

from django.conf import settings

from django.views.generic.base import TemplateView
from conectores.models import Compania


class IntercambiosListView(TemplateView):
	template_name = "intercambios.html"
	attachment_dir = settings.MEDIA_ROOT +'intercambio/'
	

	def search(self, key, value, con):

		result, data = con.search(None,key,'"{}"'.format(value))
		return data

	def get_emails(self,results_bytes, mail):

		msgs = []
		for num in results_bytes[0].split():

			type, data = mail.fetch(num, "(RFC822)")
			msgs.append(data)
			print(email_from,email_to, subject)
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
			print()
			attachment_count += 1

			fileName = part.get_filename()
			decoded_filename = str(email.header.make_header(email.header.decode_header(part.get_filename())))

			attachment_dict[decoded_filename] = part.get_payload(decode=True)

		return (attachment_count,attachment_dict)
			# print(fileName)
			# if bool(fileName):
			# 	filePath = os.path.join(self.attachment_dir, fileName)
			# 	with open(filePath, 'wb') as f:
			# 		f.write(part.get_payload(decode=True))
			# 	print('Done!!')


	def get_context_data(self, *args, **kwargs):

		context = super().get_context_data(*args, **kwargs)
		mail = imaplib.IMAP4_SSL('imap.gmail.com')
		user = self.request.user
		compania = Compania.objects.filter(owner=user).first()
		print(compania)
		assert compania.correo_intercambio, "No hay correo"
		assert compania.pass_correo_intercambio, "No hay password"
		correo = compania.correo_intercambio.strip()
		passw = compania.pass_correo_intercambio.strip()
		print(correo,passw)
		mail.login(compania.correo_intercambio,compania.pass_correo_intercambio)
		mail.list()
		print(mail.list())


		mail.select("inbox")

		result, data = mail.search(None, "ALL")
		# print(self.get_emails(data, mail))

		# Obtiene una lista de id de todos los emails
		id_list = data[0].split()
		# Obtiene el ultimo email
		latest_emails = id_list[-20:]
		email_list = []
		for element in latest_emails:

		
			result, email_data = mail.fetch(element, "(RFC822)")
		# Obtiene el binario de los emails indicados

			raw_email = email_data[0][1]
			raw_multipart = email.message_from_bytes(raw_email)
			raw_email_string = raw_email.decode('utf-8')
			email_message = email.message_from_string(raw_email_string)
			attachment_count, attachments = self.get_attachment(raw_multipart)

			email_list.append(dict(
				codigo=element.decode(),
				from_email=str(email.header.make_header(email.header.decode_header(email_message['From']))),
				subject=str(email.header.make_header(email.header.decode_header(email_message['Subject']))),
				received=str(email.header.make_header(email.header.decode_header(email_message['Received']))),
				body=self.get_body(raw_multipart).decode(),
				attachment_count=attachment_count,
				attachments=attachments

			))

		# for element in email_list:

		# 	print(json.dumps(element, sort_keys=True))
		context['lista_de_emails'] = email_list
		return context







		# email_from = str(email.header.make_header(email.header.decode_header(email_message['From'])))
		# email_to = str(email.header.make_header(email.header.decode_header(email_message['To'])))
		# subject = str(email.header.make_header(email.header.decode_header(email_message['Subject'])))
		# print(from_email, subject, received)


		# raw = email.message_from_bytes(data[0][1])
		# self.get_attachment(raw)


		# body = self.get_body(raw)
		# print(body.decode())
		# msgs = self.get_emails(self.search('FROM', 'no-reply@leetssadcode.com',mail), mail)
		# for msg in msgs:

		# 	print(self.get_body(email.message_from_bytes(msg[0][1])).decode())

		# try:
		    
		#     # if(not os.path.isdir(attachment_dir)):
		#     #     os.makedirs(settings.MEDIA_ROOT +'facturas'+'/'+self.kwargs['slug'])
		#     f = open(xml_dir+'/'+self.kwargs['slug']+'.xml','w')
		#     f.write(documento_final_firmado)
		#     f.close()
		# except Exception as e:
		#     messages.error(self.request, 'Ocurrio el siguiente Error: '+str(e))
		#     return super().form_valid(form)
		# lines = data[0]
		# print(lines[0])
		# print('//////////////////')
		# print(lines[1].decode())

		return 

# resources 
# https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
# https://docs.python.org/2/library/imaplib.html#imap4-objects
# https://rauth.readthedocs.io/en/latest/api/
# https://developers.google.com/gmail/imap/xoauth2-protocol



# email_message keys:
# ['Delivered-To', 'Received', 'X-Google-Smtp-Source', 'X-Received', 'ARC-Seal', 'ARC-Message-Signature', 'ARC-Authentication-Results', 'Return-Path', 'Received', 'Received-SPF', 'Authentication-Results', 'DKIM-Signature', 'DKIM-Signature', 'Received', 'Received', 'Content-Type', 'Date', 'From', 'Mime-Version', 'To', 'Message-ID', 'Subject', 'X-SG-EID', 'X-SG-ID', 'X-Feedback-ID']
