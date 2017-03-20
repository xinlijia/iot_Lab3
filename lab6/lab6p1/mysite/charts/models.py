from __future__ import unicode_literals

from django.db import models
import time
# Create your models here.

class chart(models.Model):
    temp = models.DecimalField(max_digits=5, decimal_places=2)
    timestamp = models.DateTimeField('date publish')

    def __str__(self):
        return str(self.temp)