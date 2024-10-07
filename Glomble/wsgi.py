
"""
WSGI config for Glomble project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/howto/deployment/wsgi/
"""

import os

from django.core.wsgi import get_wsgi_application
from whitenoise.base import WhiteNoise

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Glomble.pc_prod')

application = get_wsgi_application()
application = WhiteNoise(application)
