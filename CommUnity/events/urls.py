from django.urls import path
from .views import create_event, view_calendar,get_calendar_events,event_details,generate_event_report

urlpatterns = [
    path("create/", create_event, name="create_event"),
    path("calendar/", view_calendar, name="view_calendar"),
    path("get_calendar_events/", get_calendar_events, name="get_calendar_events"),
    path("details/<int:event_id>/", event_details, name="event_details"),
    path('events/generate-report/<int:event_id>/', generate_event_report, name='generate_event_report'),
]
