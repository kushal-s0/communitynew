from . import views
from django.urls import path

urlpatterns = [
    path('', views.home_view, name='home'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),
    path('notifications/', views.notification_view, name='notification_view'),
    path('mark_as_read/<int:announcement_id>/', views.mark_as_read, name='mark_as_read'),
    
]
