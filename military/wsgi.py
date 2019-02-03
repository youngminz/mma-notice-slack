from dotenv import find_dotenv, load_dotenv

from django.core.wsgi import get_wsgi_application

load_dotenv(find_dotenv())

application = get_wsgi_application()
