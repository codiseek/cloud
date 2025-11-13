from django import forms
from .models import Category, File
import re

class RegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'class': 'w-full bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-white'})
    )
    
    def clean_username(self):
        username = self.cleaned_data['username'].lower()
        if not re.match(r'^[a-z0-9]+$', username):
            raise forms.ValidationError("Логин должен содержать только латинские буквы в нижнем регистре и цифры")
        return username

class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ['name', 'color']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'w-full bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-white'}),
            'color': forms.TextInput(attrs={'type': 'color', 'class': 'w-full h-10 rounded-lg'}),
        }

class FileUploadForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['category', 'file']
        widgets = {
            'category': forms.Select(attrs={'class': 'w-full bg-dark-300 border border-gray-600 rounded-lg px-3 py-2 text-white'}),
        }