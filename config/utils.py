# # utils.py
# import requests
# from django.conf import settings

# def verify_recaptcha(response_token):
#     data = {
#         'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
#         'response': response_token,
#     }
#     r = requests.post('https://www.google.com/recaptcha/api/siteverify', data=data)
#     result = r.json()
#     return result.get('success', False)
