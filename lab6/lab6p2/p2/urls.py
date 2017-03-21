from django.conf.urls import url

from . import views

app_name = 'p2'
urlpatterns = [
    url(r'^$', views.hp, name='hp'),
    #url(r'(?P<city_id>[0-9]+)/$', views.detail, name='detail'),
    #url(r'(?P<city_id>[0-9]+)/weather/$', views.weather, name='weather'),
    url(r'(?P<src_id>[0-9]+)/(?P<des_id>[0-9]+)/$', views.index, name='index')
    #url(r'(?P<trip_id>[0-9]+)/results/$', views.results, name='results'),



]
