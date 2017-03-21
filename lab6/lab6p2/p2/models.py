from django.db import models


class City(models.Model):
    city_name = models.CharField(max_length=200)
    lo = models.FloatField(default=0)
    la = models.FloatField(default=0)
    temp = models.FloatField(default=0)
    def __str__(self):
        return self.city_name

class Trip(models.Model):
    src = models.CharField(max_length=200)
    des = models.CharField(max_length=200)
    def __str__(self):
        return (self.src+"->"+self.des)
