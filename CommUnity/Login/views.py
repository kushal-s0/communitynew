from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.forms import AuthenticationForm
from Login.models import UserProfile
from faculty.models import Faculty
from members.models import CoreMember, Member
from committees.models import Associations, AssociationImage
from collections import defaultdict
from django.utils import timezone
from committees.models import Announcement
from events.models import Event
# Create your views here.

def home_view(request):
    featured_images = []
    announcements = Announcement.objects.order_by('-created_at')[:5]
    upcoming_events = Event.objects.filter(date_time__gte=timezone.now(), status="approved").order_by('date_time')
    associations = Associations.objects.filter(status='approved')
    print("Announcements:", announcements)
    print("Upcoming Events:", upcoming_events)

    for association in associations:
        latest_images = association.images.order_by('-uploaded_at')[:3]
        featured_images.extend(list(latest_images))
    #check if user is logged in
    if request.user.is_authenticated:
        user = request.user
        #print (user)
        role = UserProfile.objects.get(id=user).role
        #print(role)

        #check if user is faculty
        if role == 'faculty':
            return redirect('faculty')

        else:
            #check if user is core member
            if role == 'core_member':
                user = UserProfile.objects.get(id=user)
                core_member = CoreMember.objects.get(id=user)
                print(core_member)
            return render(request, 'account/home.html', {
        'featured_images': featured_images,
        'announcements': announcements,
        'upcoming_events': upcoming_events
    })
    else:
        return render(request, 'account/home.html', {
        'featured_images': featured_images,
        'announcements': announcements,
        'upcoming_events': upcoming_events
    })

def edit_profile(request):
    user = request.user
    user_profile = UserProfile.objects.get(id=user)

    # Initialize variables to avoid UnboundLocalError
    faculty = None
    core_member = None
    member = None

    if user_profile.role == 'faculty':
        faculty = Faculty.objects.filter(id=user_profile).first()
    elif user_profile.role == 'core_member':
        core_member = CoreMember.objects.filter(id=user_profile).first()
    elif user_profile.role == 'member':
        member = Member.objects.filter(id=user_profile).first()

    context = {
        'user': user,
        'user_profile': user_profile,
        'faculty': faculty,
        'core_member': core_member,
        'member': member
    }

    if request.method == 'POST':
        user_profile.full_name = request.POST.get('full_name')
        user_profile.save()

        if user_profile.role == 'faculty':
            faculty.department = request.POST.get('department')
            faculty.designation = request.POST.get('designation')
            faculty.save()
        elif user_profile.role == 'core_member':
            core_member.club = request.POST.get('club')
            core_member.position = request.POST.get('position')
            core_member.save()
        elif user_profile.role == 'member':
            member.club = request.POST.get('club')
            member.position = request.POST.get('position')
            member.save()

        return redirect('home')
    
    return render(request, 'account/edit_profile.html', context)

