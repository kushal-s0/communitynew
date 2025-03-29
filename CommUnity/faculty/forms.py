from django import forms
from events.models import FacultyLockDate

class FacultyLockDateForm(forms.ModelForm):
    class Meta:
        model = FacultyLockDate
        fields = ['locked_date', 'reason']
        widgets = {
            'locked_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'reason': forms.TextInput(attrs={'class': 'form-control'}),
        }
