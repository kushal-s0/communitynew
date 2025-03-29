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
    return render(request, "events/event_details.html", {"event": event})


@login_required
def create_event(request):
    current_user = request.user
    user_profile = current_user.userprofile
    try:
        core_member = CoreMember.objects.get(id=user_profile)
    except CoreMember.DoesNotExist:
        messages.error(request, "Only core members can create events.")
        return redirect("view_calendar")
    if not core_member.assosiation:
        messages.error(request, "You must be a member of an association to create events.")
        return redirect("view_calendar")
    locations = Location.objects.all()

    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        date_time = datetime.strptime(request.POST["date_time"], "%Y-%m-%dT%H:%M")
        location_id = request.POST["location"]
        duration = int(request.POST["duration"])

        location = Location.objects.get(id=location_id)
        # date_time = make_aware(datetime.datetime.strptime(date_time, "%Y-%m-%dT%H:%M"))
        event_end_time = date_time + timedelta(hours=duration)

        # location = get_object_or_404(Location, id=location_id)
        # Automatically assign club from Core Member
        ass = core_member.assosiation  
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
            assosiation=ass,
            created_by=user_profile,
            status="pending"  # Awaiting faculty approval
        )

        # Notify faculty in charge
        faculty_incharge = ass.faculty_incharge
        send_mail(
            subject=f"Approval Required for Event: {title}",
            message=f"Dear {faculty_incharge.id.full_name},\n\n"
                    f"A new event '{title}' has been created by {request.user.get_full_name()} "
                    f"for the assosiation '{ass.name}'. Please review and approve it.\n\n",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[faculty_incharge.id.id.email],
            fail_silently=False,
        )

        messages.success(request, "Event submitted for approval!")
        return redirect("view_calendar")

    return render(request, "events/create_event.html", {"locations":locations})



def view_calendar(request):
    events = Event.objects.filter(status="approved")
    return render(request, "events/view_calendar.html", {"events": events})
