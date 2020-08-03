import os

from dotenv import find_dotenv, load_dotenv

from django.core.exceptions import ImproperlyConfigured

load_dotenv(find_dotenv())


def get_env_variable(var_name, default=None):
    try:
        return os.environ[var_name]

    except KeyError:
        if default is None:
            error_msg = f"필수 환경 변수 {var_name}가 설정되지 않았습니다."
            raise ImproperlyConfigured(error_msg)

        return default


SECRET_KEY = get_env_variable("SECRET_KEY")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ALLOWED_HOSTS = ["*"]

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = []

LOCAL_APPS = ["users.apps.UsersConfig", "notice.apps.NoticeConfig"]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "military.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]

WSGI_APPLICATION = "military.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": get_env_variable(
            "DATABASE_ENGINE", default="django.db.backends.mysql"
        ),
        "NAME": get_env_variable("DATABASE_NAME"),
        "USER": get_env_variable("DATABASE_USER"),
        "PASSWORD": get_env_variable("DATABASE_PASSWORD"),
        "HOST": get_env_variable("DATABASE_HOST"),
        "PORT": get_env_variable("DATABASE_PORT", default="3306"),
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

AUTH_USER_MODEL = "users.User"

LANGUAGE_CODE = "ko"

TIME_ZONE = "Asia/Seoul"

USE_I18N = True

USE_L10N = True

USE_TZ = False

STATIC_URL = "/static/"

STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

STATIC_ROOT = os.path.join(BASE_DIR, "military/staticfiles")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(levelname)-5s %(asctime)s %(name)s:%(lineno)s %(funcName)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        }
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        }
    },
    "loggers": {
        "django": {"handlers": ["console"], "propagate": True},
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
            "formatter": "verbose",
        },
        "django.db.backends": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
            "formatter": "verbose",
        },
        "raven": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
            "formatter": "verbose",
        },
        "sentry.errors": {
            "handlers": ["console"],
            "level": "DEBUG",
            "propagate": False,
            "formatter": "verbose",
        },
    },
}

for local_app_folder in [local_app.split(".")[0] for local_app in LOCAL_APPS]:
    LOGGING["loggers"][local_app_folder] = {
        "handlers": ["console"],
        "level": "DEBUG",
        "propagate": True,
        "formatter": "verbose",
    }

SLACK_INCOMING_WEBHOOK_URL = get_env_variable("SLACK_INCOMING_WEBHOOK_URL")
MMA_LOCATION = get_env_variable("MMA_LOCATION", "서울청")
MMA_LOCATION_LIST = ["병무청", MMA_LOCATION]
