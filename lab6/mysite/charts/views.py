from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from change_temp import add
from charts.models import chart

# Create your views here.
def showchart(request):
    if add():
	temperature = []
	t = chart.objects.all()
	tt = t.order_by('floattime').reverse()
	count = 0
        while count<10:
	    temperature.append(tt[count])
	    count += 1
        return render(request, 'charts/chart.html',{'temperature':temperature})

