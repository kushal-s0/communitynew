from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Event, FacultyLockDate
from .google_calendar import create_google_calendar_event
from django.conf import settings
from django.core.mail import send_mail
from .models import Faculty , CoreMember

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

    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        date_time = request.POST["date_time"]
        location = request.POST["location"]

        # Automatically assign club from Core Member
        ass = core_member.assosiation  

        event = Event.objects.create(
            title=title,
            description=description,
            date_time=date_time,
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

    return render(request, "events/create_event.html")



# @login_required
# def approve_event(request, event_id):
#     event = get_object_or_404(Event, id=event_id)
#     if request.user.is_faculty and request.user.faculty.club == event.club:
#         event.status = "approved"
#         event.approved_by = request.user
#         event.google_calendar_event_id = create_google_calendar_event(event)
#         event.save()
#         messages.success(request, "Event approved and added to Google Calendar!")
#     return redirect("view_calendar")

@login_required
def view_calendar(request):
    events = Event.objects.filter(status="approved")
    return render(request, "events/view_calendar.html", {"events": events})
