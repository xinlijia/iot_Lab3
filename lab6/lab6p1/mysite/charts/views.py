from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from change_temp import add
from charts.models import chart

# Create your views here.
def showchart(request):
    if add():
	temperature = chart.objects.all()
        return render(request, 'charts/showchart.html',{'temperature':temperature})

