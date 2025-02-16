# users/emails.py
import logging
from django.template.loader import render_to_string
from djoser.email import PasswordResetEmail, ActivationEmail
from urllib.parse import urlsplit

logger = logging.getLogger(__name__)

class CustomPasswordResetEmail(PasswordResetEmail):
    template_name = 'emails/custom_password_reset.html'

    def get_context_data(self):
        context = super().get_context_data()
        uid = context.get('uid')
        token = context.get('token')

        # Construct the base URL dynamically
        full_url = self.request.build_absolute_uri('/')
        parsed_url = urlsplit(full_url)
        if parsed_url.hostname == "example.com":
            base_url = f"{parsed_url.scheme}://{parsed_url.hostname}"
        else:
            base_url = f"{parsed_url.scheme}://{parsed_url.hostname}:3000"

        # Construct the reset link
        reset_link = f"{base_url}/password-reset/{uid}/{token}"
        context["reset_link"] = reset_link
        return context

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        email_body = render_to_string(self.template_name, context)
        logger.debug("Rendered password reset email body: %s", email_body)

        self.body = email_body
        self.content_subtype = "html"
        self.subject = "Password Reset Request"
        super().send(to, *args, **kwargs)

# users/emails.py
from djoser.email import ActivationEmail
from urllib.parse import urlsplit

class CustomActivationEmail(ActivationEmail):
    def get_context_data(self):
        context = super().get_context_data()
        uid = context.get('uid')
        token = context.get('token')

        # Determine the base URL dynamically or use a fallback
        if hasattr(self, 'request') and self.request:
            full_url = self.request.build_absolute_uri('/')
            parsed_url = urlsplit(full_url)

            # Construct the base URL and add port 3000 for non-example.com domains
            if parsed_url.hostname == "example.com":
                base_url = f"{parsed_url.scheme}://{parsed_url.hostname}"
                self.template_name = "emails/tenant_activation_email.html"
            else:
                base_url = f"{parsed_url.scheme}://{parsed_url.hostname}:3000"
                self.template_name = "emails/user_activation_email.html"
        else:
            # Fallback if no request context (assume example.com as a default)
            base_url = "http://example.com:3000"
            self.template_name = "emails/user_activation_email.html"

        # Construct the activation link with the proper base URL
        activation_link = f"{base_url}/activation/{uid}/{token}"
        context["activation_link"] = activation_link
        return context

    def send(self, to, *args, **kwargs):
        context = self.get_context_data()
        email_body = render_to_string(self.template_name, context)
        
        # Log the email body for debugging purposes
        logger.debug("Rendered activation email body: %s", email_body)

        self.body = email_body
        self.content_subtype = "html"
        self.subject = "Activate Your Account"
        super().send(to, *args, **kwargs)



