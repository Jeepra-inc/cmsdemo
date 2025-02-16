import requests
from django.conf import settings
from rest_framework.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

def verify_turnstile(token):
    """
    Verify the Turnstile CAPTCHA token using Cloudflare's API.
    """
    url = "https://challenges.cloudflare.com/turnstile/v0/siteverify"
    payload = {
        "secret": settings.TURNSTILE_SECRET_KEY,  # Your Turnstile secret key
        "response": token,                        # Token from the frontend
    }
    response = requests.post(url, data=payload)
    result = response.json()

    if not result.get("success"):
        # Log the failure reason for debugging
        logger.error(f"Turnstile validation failed: {result}")
        raise ValidationError("Invalid CAPTCHA. Please try again.")

    return result

