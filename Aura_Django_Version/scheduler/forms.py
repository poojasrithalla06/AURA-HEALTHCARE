from django import forms
from django.contrib.auth.models import User
from .models import Task, HealthMetric, FamilyContact, MedicalImage

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ['title', 'description', 'due_date', 'priority']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'What needs to be done?'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Details (optional)'}),
            'due_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
        }

class HealthMetricForm(forms.ModelForm):
    class Meta:
        model = HealthMetric
        fields = ['metric_type', 'value']
        widgets = {
            'metric_type': forms.Select(attrs={'class': 'form-control'}),
            'value': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter value (e.g., 120/80, 72 bpm, 98.6 F)'}),
        }

class MedicalImageForm(forms.ModelForm):
    class Meta:
        model = MedicalImage
        fields = ['image', 'image_type']

class FamilyContactForm(forms.ModelForm):
    class Meta:
        model = FamilyContact
        fields = ['name', 'phone_number', 'email']

class DietPlanForm(forms.Form):
    GOAL_CHOICES = [
        ('weight_loss', 'Weight Loss'),
        ('muscle_gain', 'Muscle Gain'),
        ('diabetes_friendly', 'Diabetes Friendly'),
        ('heart_healthy', 'Heart Healthy'),
        ('balanced', 'Balanced Diet'),
    ]
    goal = forms.ChoiceField(choices=GOAL_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

class UserUpdateForm(forms.ModelForm):
    email = forms.EmailField()

    class Meta:
        model = User
        fields = ['username', 'email']
