from django.shortcuts import render
from django.http import HttpResponseRedirect, HttpResponse
from change_temp import add

# Create your views here.
def showchart(request):
    if add():
        return render(request, 'charts/showchart.html')

