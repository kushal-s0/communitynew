from django.urls import path
from .views import create_event, view_calendar

urlpatterns = [
    path("create/", create_event, name="create_event"),
    # path("approve/<int:event_id>/", approve_event, name="approve_event"),
    path("calendar/", view_calendar, name="view_calendar"),
]
