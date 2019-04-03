import imaplib, email, os
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
		return msgs

	def get_body(self, msg):

		if msg.is_multipart():
			return self.get_body(msg.get_payload(0))
		else:
			return msg.get_payload(None, True)

	def get_attachment(self, msg):

		for part in msg.walk():
			print(part)
		# 	if part.get_content_maintype() == 'multipart':
		# 		continue
		# 	if part.get('Content-Disposition') is None:
		# 		continue
			# fileName = part.get_filename()
			# print(fileName)
			# print("Este es el filename ", b64decode(fileName))
			# if bool(fileName):
			# 	filePath = os.path.join(self.attachment_dir, fileName)
			# 	with open(filePath, 'wb') as f:
			# 		f.write(part.get_payload(decode=True))
			# 	print('Done!!')


	def get_context_data(self, *args, **kwargs):

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
		id_list = data[0].split()
		latest_email = id_list[-1]
		result, data = mail.fetch(latest_email, "(RFC822)")
		raw = email.message_from_bytes(data[0][1])
		self.get_attachment(raw)


		body = self.get_body(raw)
		print(body.decode())
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




