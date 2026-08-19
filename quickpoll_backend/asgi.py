"""
ASGI config for quickpoll_backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/6.1/howto/deployment/asgi/
"""

import os

from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'quickpoll_backend.settings')

# Initialize Django ASGI application early to ensure AppRegistry is populated
# before importing consumers or routing that depend on Django models.
django_asgi_app = get_asgi_application()

# Import consumers AFTER get_asgi_application() so the app registry is ready.
from django.urls import re_path  # noqa: E402

from polls.consumers import PollConsumer  # noqa: E402

application = ProtocolTypeRouter({
    'http': django_asgi_app,
    'websocket': URLRouter([
        re_path(r'^ws/polls/(?P<poll_id>\d+)/$', PollConsumer.as_asgi()),
    ]),
})

