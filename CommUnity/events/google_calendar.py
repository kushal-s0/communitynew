from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv
import os
from datetime import timedelta
load_dotenv()
SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "community-450615-ea7ca3c3bfa3.json"
CALENDAR_ID = os.getenv("CALENDAR_ID")

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
        "end": {
            "dateTime": (event.date_time + timedelta(hours=event.duration)).isoformat(),
            "timeZone": "Asia/Kolkata",
        },
        "location": event.location.location,
    }
    created_event = service.events().insert(calendarId=CALENDAR_ID, body=event_data).execute()
    return created_event.get("id")

def delete_google_calendar_event(event_id):
    service = get_calendar_service()
    service.events().delete(calendarId=CALENDAR_ID, eventId=event_id).execute()
