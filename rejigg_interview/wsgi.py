import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "rejigg_interview.settings")

application = get_wsgi_application()


