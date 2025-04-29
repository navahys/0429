from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('about/', views.about_view, name='about'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('voice-settings/', views.voice_settings_view, name='voice_settings'),
    path('support-resources/', views.support_resources_view, name='support_resources'),
]

# Custom error handlers
handler404 = 'core.views.handler404'
handler500 = 'core.views.handler500'
