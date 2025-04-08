
from django import forms

class EventReportForm(forms.Form):
    organizer = forms.CharField(max_length=255, label="Event Organizer")
    event_type = forms.CharField(max_length=255, label="Event Type (Workshop, Seminar, etc.)")
    attendees = forms.IntegerField(label="Number of Attendees")
    speakers = forms.CharField(widget=forms.Textarea, label="List of Speakers")
    agenda = forms.CharField(widget=forms.Textarea, label="Agenda")
    outcomes = forms.CharField(widget=forms.Textarea, label="Key Outcomes or Results")
    media_links = forms.CharField(widget=forms.Textarea, label="Links to Event Media (Photos, Videos, etc.)")
