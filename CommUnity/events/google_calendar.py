from google.oauth2 import service_account
from googleapiclient.discovery import build
import os
from datetime import timedelta

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "community-450615-ea7ca3c3bfa3.json"
CALENDAR_ID = "3e02edeecbfa963eb96a7e4108ec4a1111a17b7a19605768bbec37f2a007ee43@group.calendar.google.com"

def get_calendar_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES
    )
    return build("calendar", "v3", credentials=credentials)

def create_google_calendar_event(event):
    service = get_calendar_service()
    event_data = {
        "summary": event.title,
        "description": event.description,
        "start": {"dateTime": event.date_time.isoformat(), "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": (event.date_time + timedelta(hours=2)).isoformat(), "timeZone": "Asia/Kolkata"},
        "location": event.location
    }
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event_data).execute()
    return created_event.get("id")

def delete_google_calendar_event(event_id):
    service = get_calendar_service()
    service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
