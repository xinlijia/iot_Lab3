from django import forms

class Plan(forms.Form):
	src=forms.CharField(label='src', max_length=100)
	des=forms.CharField(label='des', max_length=100)



