from django.shortcuts import render,get_object_or_404,redirect
from faculty.models import Faculty
from committees.models import Associations
from Login.models import UserProfile
from members.models import CoreMember, Member
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from events.models import Event
from django.db.models import Q
from events.google_calendar import create_google_calendar_event
from django.contrib.auth import get_user_model
from events.models import FacultyLockDate
from .forms import FacultyLockDateForm
User = get_user_model()

# Create your views here.

def faculty_view(request):
    return render(request, 'faculty.html')
def profile_view(request):   
    active_user = request.user
    user = get_object_or_404(User, username=active_user.username)
    print(user.email)
    user_profile = get_object_or_404(UserProfile, id=user)
    faculty = Faculty.objects.get(id=user_profile)
    associations = Associations.objects.filter(faculty_incharge=faculty)
    print(associations)
    context = {'user': user,'user_profile': user_profile,'faculty': faculty,'associations': associations}
    return render(request, 'profile.html', context)
def committee_member_view(request, pk):
    committee = get_object_or_404(Associations, pk=pk)

    # Fetch all members and filter manually
    all_members = Member.objects.all()
    members = [member for member in all_members if pk in member.association]  # Assuming association is a list

    # Fetch core members normally
    core_members = CoreMember.objects.filter(association=committee)

    context = {
        'committee': committee,
        'members': members,
        'core_members': core_members
    }

    print(context)  # Debugging

    return render(request, 'committee_member.html', context)


def faculty_committee(request):
    try:
        user = request.user
        user_profile = get_object_or_404(UserProfile, id=user)
        faculty = Faculty.objects.get(id=user_profile)
        
        
        from django.db.models import Q
        associations = Associations.objects.filter(faculty_incharge=faculty)
        
        clubs = [a for a in associations if a.type == 'clubs']
        committees = [a for a in associations if a.type == 'committees']
                
        request.session['url'] = 'faculty_committee'
        content = {'clubs': clubs, 'comm': committees}
        return render(request, 'committee.html', content)
    

    except (UserProfile.DoesNotExist, Faculty.DoesNotExist):
        # Handle case where user isn't associated with faculty
        content = {'clubs': [], 'comm': []}
        return render(request, 'committee.html', content)

@csrf_exempt  # Use this only if CSRF protection is disabled; otherwise, use CSRF token
def search_students(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '').lower()

        students = UserProfile.objects.filter(
            (Q(name__icontains=query) | Q(email__icontains=query)) & 
            (Q(role='non_participant') | Q(role='member'))
        )
        student_list = [{'name': student.name, 'email': student.email} for student in students]

        return JsonResponse({'students': student_list})

    return JsonResponse({'error': 'Invalid request'}, status=400)
def add_core_member_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        query = data.get('query', '').lower()

        if query:
            # Filter users based on username OR email
            users = get_user_model().objects.filter(Q(username__icontains=query) | Q(email__icontains=query))

            # Get matching UserProfile records for these users
            students = UserProfile.objects.filter(
                Q(id__in=users.values_list('id', flat=True)) &
                (Q(role='non_participating') | Q(role='member'))
            )

            # Serialize data
            student_list = [{'id': student.id.username, 'name': student.full_name, 'email': student.id.email} for student in students]

            return JsonResponse({'students': student_list})
    
    all_students = UserProfile.objects.all()
    return render(request, 'add_core_member.html', {'all_students': all_students})

def select_student(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            student_id = data.get('student_id')

            if not student_id:
                return JsonResponse({'message': 'Student ID not provided'}, status=400)

            # Fetch the student from the database (modify based on your model structure)
            student = get_object_or_404(User, username=student_id)  # Assuming username is the student ID
            student_user = get_object_or_404(UserProfile, id=student)
            print(student_user)
            student_user.role = 'core_member'
            student_user.save()

            # core_update = CoreMember.objects.create(id=student_user)
            # core_update.save()
            # Do something with the selected student (e.g., add to a list, update, etc.)
            # Example: Returning student details
            return JsonResponse({
                'message': f'Student {student.username} selected successfully!',
                'student': {
                    'id': student.username,
                    'email': student.email,
                }
            })

        except User.DoesNotExist:
            return JsonResponse({'message': 'Student not found'}, status=404)
        except Exception as e:
            return JsonResponse({'message': str(e)}, status=500)

    return render(request, 'add_core_member.html')

@login_required
def approve_clubs(request):
    if not request.user.is_authenticated:
        return HttpResponse("You must be logged in")

    try:
        faculty_user = get_object_or_404(UserProfile, id=request.user)
        faculty = get_object_or_404(Faculty, id=faculty_user)  

        # Fetch pending requests
        pending_clubs = Associations.objects.filter(status='pending', faculty_incharge=faculty)
        delete_requests = Associations.objects.filter(status='delete_pending', faculty_incharge=faculty)
        event_requests  = Event.objects.filter(status='pending', association__faculty_incharge=faculty)

        if request.method == "POST":
            action = request.POST.get("action")

            if action in ["approve", "reject", "approve_delete"]:
                club_id = request.POST.get("club_id")
                club = get_object_or_404(Associations, id=club_id)

                # Ensure only assigned faculty can approve/reject
                if club.faculty_incharge != faculty:
                    return HttpResponse("You are not authorized to approve/reject this request.")

                if action == "approve":
                    club.status = "approved"
                elif action == "reject":
                    if club.status == "delete_pending":
                        club.status = "approved"
                    else:
                        club.status = "rejected"
                elif action == "approve_delete":
                    club.delete()
                    return redirect("approve_clubs")

                club.save()

            elif action in ["approve_event", "reject_event"]:
                event_id = request.POST.get("event_id")
                event = get_object_or_404(Event, id=event_id)

                # Ensure only assigned faculty can approve/reject
                if event.association.faculty_incharge != faculty:
                    return HttpResponse("You are not authorized to approve/reject this event.")

                if action == "approve_event":
                    event.status = "approved"
                    event.approved_by = faculty

                    # Try to add event to Google Calendar
                    try:
                        event.google_calendar_event_id = create_google_calendar_event(event)
                        messages.success(request, f"Event '{event.title}' approved and added to Google Calendar!")
                    except Exception as e:
                        messages.error(request, f"Event approved but failed to add to Google Calendar: {e}")

                elif action == "reject_event":
                    event.status = "rejected"
                    messages.warning(request, f"Event '{event.title}' has been rejected.")

                event.save()

            return redirect("approve_clubs")

        return render(request, "approve_clubs.html", {
            "pending_clubs": pending_clubs,
            "delete_requests": delete_requests,
            "event_requests": event_requests,  # Make sure this is passed to the template
            "faculty": faculty
        })

    except UserProfile.DoesNotExist:
        return HttpResponse("User profile not found")
    except Faculty.DoesNotExist:
        return HttpResponse("Faculty profile not found")
    
def manage_faculty_lock_dates(request):
    if request.method == "POST":
        form = FacultyLockDateForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Date locked successfully!")
            return redirect('manage_faculty_lock_dates')
        else:
            messages.error(request, "Error locking the date. Please check your input.")

    lock_dates = FacultyLockDate.objects.all().order_by('locked_date')
    form = FacultyLockDateForm()
    return render(request, 'faculty_lock_date.html', {'lock_dates': lock_dates, 'form': form})