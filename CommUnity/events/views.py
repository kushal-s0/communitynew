from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, FacultyLockDate
from .google_calendar import create_google_calendar_event
from django.conf import settings
from django.core.mail import send_mail
from .models import Faculty , CoreMember, Location
from datetime import datetime, timedelta
from django.utils.timezone import make_aware
from django.http import JsonResponse
from django.conf import settings
from django.utils.timezone import now,localtime
from .forms import EventReportForm
from fpdf import FPDF
from reportlab.pdfgen import canvas
from django.http import FileResponse
from django.db import models
from django.utils import timezone
import os
import requests
from django.core.files.base import ContentFile
from .forms import EventReportForm
from xhtml2pdf import pisa
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from django.views.decorators.clickjacking import xframe_options_exempt

def get_calendar_events(request):
    events = Event.objects.filter(status="approved")
    event_list = [
        {   
            "id": event.id,
            "title": event.title,
            "start": event.date_time.isoformat(),
            "end": (event.date_time + timedelta(hours=event.duration)).isoformat(),
            "location": event.location.location,
            "details_url": f"/events/details/{event.id}/",
        }
        for event in events
    ]
    
    return JsonResponse(event_list, safe=False)

def event_details(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    event.end_time = event.date_time + timedelta(hours=event.duration)
    end_time_ist = localtime(event.end_time)
    now_ist = localtime(now())
    event_over = end_time_ist < now_ist
    return render(request, "events/event_details.html", {"event": event,"end_time_ist": end_time_ist,"now_ist": now_ist,"event_over": event_over})

@login_required
def create_event(request):
    current_user = request.user
    user_profile = current_user.userprofile
    try:
        core_member = CoreMember.objects.get(id=user_profile)
    except CoreMember.DoesNotExist:
        messages.error(request, "Only core members can create events.")
        return redirect("view_calendar")
    if not core_member.association:
        messages.error(request, "You must be a member of an association to create events.")
        return redirect("view_calendar")
    locations = Location.objects.all()

    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        date_time = make_aware(datetime.strptime(request.POST["date_time"], "%Y-%m-%dT%H:%M"))
        location_id = request.POST["location"]
        duration = int(request.POST["duration"])

        location = Location.objects.get(id=location_id)
        # date_time = make_aware(datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M"))
        event_end_time = date_time + timedelta(hours=duration)

        # location = get_object_or_404(Location, id=location_id)
        # Automatically assign club from Core Member
        ass = core_member.association  
        if FacultyLockDate.objects.filter(locked_date=date_time.date()).exists():
            messages.error(request, "This date is locked by faculty and cannot have events.")
            return redirect("create_event")
        overlapping_events = Event.objects.filter(
            location=location,
            status="approved",
            date_time__lt=event_end_time,
            date_time__gte=date_time
        )
        for event in overlapping_events:
            existing_event_end_time = event.date_time + timedelta(hours=event.duration)

            if (date_time < existing_event_end_time and event.date_time < event_end_time):
                messages.error(request, "This location is already booked during the selected time.")
                return redirect("create_event")

        event = Event.objects.create(
            title=title,
            description=description,
            date_time=date_time,
            duration=duration,
            location=location,
            association=ass,
            created_by=user_profile,
            status="pending"  # Awaiting faculty approval
        )

        # Notify faculty in charge
        faculty_incharge = ass.faculty_incharge
        send_mail(
            subject=f"Approval Required for Event: {title}",
            message=f"Dear {faculty_incharge.id.full_name},\n\n"
                    f"A new event '{title}' has been created by {request.user.get_full_name()} "
                    f"for the association '{ass.name}'. Please review and approve it.\n\n",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[faculty_incharge.id.id.email],
            fail_silently=False,
        )

        messages.success(request, "Event submitted for approval!")
        return redirect("view_calendar")

    return render(request, "events/create_event.html", {"locations":locations})


@xframe_options_exempt
def view_calendar(request):
    events = Event.objects.filter(status="approved")
    return render(request, "events/view_calendar.html", {"events": events})

def generate_report_with_huggingface(prompt):
    API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
    headers = {
        "Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"
    }
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens": 1000}
    }
    response = requests.post(API_URL, headers=headers, json=payload)
    
    if response.status_code == 200:
        result = response.json()
        if isinstance(result, list):
            full_output = result[0]["generated_text"]
        elif "generated_text" in result:
            full_output = result["generated_text"]
        else:
            raise Exception("Unexpected Hugging Face response format.")
        
        if full_output.strip().startswith(prompt.strip()):
            return full_output.replace(prompt.strip(), "").strip()
        return full_output.strip()
    elif isinstance(result, dict) and "error" in result:
        raise Exception(f"Hugging Face Error: {result['error']}")
        
    raise Exception(f"Hugging Face API error: {response.status_code}, {response.text}")

@login_required
def generate_event_report(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    print("VIEW REACHED")

    if request.method == "POST":
        print("POST REQUEST DETECTED")
        form = EventReportForm(request.POST)
        if form.is_valid():
            print("FORM IS VALID")
            data = form.cleaned_data

            # Construct the prompt
            prompt = f"""
                        Write a detailed and professional event report for the following:

                        Event Name: {event.title}
                        Date: {event.date_time.date()}
                        Time: {event.date_time.time()}
                        Location: {event.location}
                        Organizer: {data['organizer']}
                        Type: {data['event_type']}
                        Number of Attendees: {data['attendees']}
                        Speakers: {data['speakers']}
                        Agenda of the Event: {data['agenda']}
                        Outcomes of the Event: {data['outcomes']}
                        Media Links: {data['media_links']}

                        The report should summarize the key points of the event, the success of the session, speaker contributions, and outcomes.
                        """


            try:
                print("SENDING REQUEST TO HUGGING FACE")
                # Call Hugging Face
                report = generate_report_with_huggingface(prompt)
                print("RESPONSE RECEIVED")

                # Save to model
                event.report_content = report
                event.report_generated = True
                event.report_generated_at = now()

                buffer = BytesIO()
                filename = f"event_report_{event.id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                doc = SimpleDocTemplate(buffer, pagesize=A4)
                styles = getSampleStyleSheet()
                story = []

                story.append(Paragraph("Event Report", styles["Title"]))
                story.append(Spacer(1, 12))

                for para in report.split("\n"):
                    story.append(Paragraph(para.strip(), styles["BodyText"]))
                    story.append(Spacer(1, 12))

                doc.build(story)
                buffer.seek(0)

                event.report_pdf.save(filename, ContentFile(buffer.read()))
                event.save()

                messages.success(request, "Report generated successfully.")
                return redirect("event_details", event_id=event.id)

            except Exception as e:
                print("ERROR:", str(e))
                messages.error(request, f"Error generating report: {str(e)}")
                return render(request, "events/generate_report_form.html", {"form": form, "event": event})
        else:
            print("FORM IS NOT VALID")  # ✅ form error test
            print(form.errors)
    else:
        form = EventReportForm()

    return render(request, "events/generate_report_form.html", {"form": form, "event": event})
