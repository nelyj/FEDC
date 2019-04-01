import imaplib

from django.views.generic.base import TemplateView
from conectores.models import Compania


class IntercambiosListView(TemplateView):
	template_name = "intercambios.html"
	

	def get_context_data(self, *args, **kwargs):

		mail = imaplib.IMAP4_SSL('imap.gmail.com')
		user = self.request.user
		compania = Compania.objects.filter(owner=user).first()
		print(compania)
		assert compania.correo_intercambio, "No hay correo"
		assert compania.pass_correo_intercambio, "N o hay password"
		correo = compania.correo_intercambio.strip()
		passw = compania.pass_correo_intercambio.strip()
		print(correo,passw)
		mail.login('code4road@gmail.com', 'gmaiSeneca88+')
		mail.list()
		mail.select("inbox")
		result, data = mail.search(None, "ALL")
		id_list = data[0].split()
		latest_email = id_list[-1]
		result, data = mail.fetch(latest_email, "(RFC822)")
		lines = data[0]
		print(lines[0])
		print('//////////////////')
		print(lines[1].decode())

		return 

# resources 
# https://yuji.wordpress.com/2011/06/22/python-imaplib-imap-example-with-gmail/
# https://docs.python.org/2/library/imaplib.html#imap4-objects