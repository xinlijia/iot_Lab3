from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.core.urlresolvers import reverse
from .forms import Plan
import requests

from .models import City, Trip

def index(request, src_id, des_id):
	city_list = City.objects.order_by('city_name')[:5]
	# context = {'city_list': city_list}
	for city in city_list:
		if(city.city_name=="New York"):
			r = requests.get('http://api.openweathermap.org/data/2.5/weather?q=New%20York&APPID=bb740b159467f35d8fe7b27bb6bcf553')
		elif(city.city_name=="Boston"):
			r = requests.get('http://api.openweathermap.org/data/2.5/weather?q=Boston&APPID=bb740b159467f35d8fe7b27bb6bcf553')
		elif(city.city_name=="Philadelphia"):
			r = requests.get('http://api.openweathermap.org/data/2.5/weather?q=Philadelphia&APPID=bb740b159467f35d8fe7b27bb6bcf553')
		else:
			r = requests.get('http://api.openweathermap.org/data/2.5/weather?q=Washington&APPID=bb740b159467f35d8fe7b27bb6bcf553')
		city.temp=(r.json()['main']['temp'])
		city.save()

	# question = get_object_or_404(Question, pk=question_id)
	src = get_object_or_404(City, pk=src_id)
	dest = get_object_or_404(City, pk=des_id)
	context = {'source': src, 'dest': dest}
	return render(request, 'p2/route.html', context)


def hp(request):
	return render(request, 'p2/route.html')

# def results(request, src_id=0, des_id=0):
#     # Apply Google Map here
#     city_src=get_object_or_404(pk=src_id)
#     city_des=get_object_or_404(pk=des_id)
#
#     return HttpResponseRedirect('/p2')
#
#
#
#
# <<<<<<< Updated upstream
# =======
#
# def trip(request):
#     if request.method == 'POST':
#         form = Plan(request.POST)
#         if form.is_valid():
#             New_trip=Trip(src=form.cleaned_data['src'],des=form.cleaned_data['des'])
#             New_trip.save()
#             #edit to redirect to Google Map here
#             return HttpResponseRedirect('/p2')
#         else:
#             form = Plan()
#         return render(request, 'p2/plan.html', {'form': form})
# >>>>>>> Stashed changes
