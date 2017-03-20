from django.contrib import admin

# Register your models here.

from .models import City, Trip

admin.site.register(City)
admin.site.register(Trip)

