"""
WSGI config for lms_project project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.0/howto/deployment/wsgi/
"""

import os
import sys

# Add the project directory to the sys.path
path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if path not in sys.path:
    sys.path.append(path)

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lms_project.settings')

application = get_wsgi_application()

# Run migrations automatically on Vercel startup if using SQLite
if os.environ.get('VERCEL'):
    from django.core.management import call_command
    try:
        call_command('migrate', '--noinput')
    except Exception as e:
        print(f"Migration failed on startup: {e}")

app = application
