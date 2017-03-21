from __future__ import unicode_literals

from django.db import models
import time
# Create your models here.

class chart(models.Model):
    temp = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    timestamp = models.CharField(max_length=100, default="Null")
    floattime = models.DecimalField(max_digits=13, decimal_places=3, default=0)

    def __str__(self):
        return str(self.temp)
