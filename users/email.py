from templated_mail.mail import BaseEmailMessage


class AccountCreateEmail(BaseEmailMessage):
    template_name = 'email/account_create.html'

    def get_context_data(self):
        """
        """
        context = super(AccountCreateEmail, self).get_context_data()

        user = context.get('user')
        password = context.get('password')
        return context
