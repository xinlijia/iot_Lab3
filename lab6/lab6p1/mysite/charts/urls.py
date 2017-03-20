from django.conf.urls import url
from views import showchart

urlpatterns = [
    url(r'^showchart/', showchart, name='showchart'),
]