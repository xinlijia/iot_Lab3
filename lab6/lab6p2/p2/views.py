from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from .forms import Plan

from .models import City, Trip

def index(request):
    city_list = City.objects.order_by('city_name')[:5]
    context = {'city_list': city_list}
    return render(request, 'p2/index.html', context)


def weather(request, city_id):
    city = get_object_or_404(City, pk=city_id)
    response = "Weather of City %s."
    # Apply weather Api here
    return render(request, 'p2/weather.html', {'city': city})

def results(request, trip_id):
    # Apply Google Map here
    response = "You're looking at the results of trip %s."
    return HttpResponse(response % trip_id)






def trip(request):
    if request.method == 'POST':
        form = Plan(request.POST)
        if form.is_valid():
            New_trip=Trip(src=form.cleaned_data['src'],des=form.cleaned_data['des'])
            New_trip.save()
            #edit to redirect to Google Map here
            return HttpResponseRedirect('/p2')
        else:
            form = Plan()
        return render(request, 'p2/plan.html', {'form': form})


