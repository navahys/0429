from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import DetailView, UpdateView
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import CustomUser, MoodRecord
from .forms import UserProfileForm, MoodRecordForm
from .serializers import UserSerializer, MoodRecordSerializer

# 기존 API ViewSet 클래스 유지
class UserViewSet(viewsets.ModelViewSet):
    """API viewset for user profile operations"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own profile
        return CustomUser.objects.filter(id=self.request.user.id)
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['patch'])
    def update_preferences(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class MoodRecordViewSet(viewsets.ModelViewSet):
    """API viewset for mood records"""
    queryset = MoodRecord.objects.all()
    serializer_class = MoodRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Users can only see their own mood records
        return MoodRecord.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return mood statistics for the user"""
        mood_records = MoodRecord.objects.filter(user=self.request.user)
        mood_stats = {
            'very_bad': mood_records.filter(mood='very_bad').count(),
            'bad': mood_records.filter(mood='bad').count(),
            'neutral': mood_records.filter(mood='neutral').count(),
            'good': mood_records.filter(mood='good').count(),
            'very_good': mood_records.filter(mood='very_good').count(),
        }
        return Response(mood_stats)

# 감정 기록 관련 웹 뷰
@login_required
def record_mood_view(request):
    """View for recording user's mood"""
    if request.method == 'POST':
        form = MoodRecordForm(request.POST)
        if form.is_valid():
            mood_record = form.save(commit=False)
            mood_record.user = request.user
            mood_record.save()
            messages.success(request, "감정 상태가 성공적으로 기록되었습니다.")
            return redirect('dashboard')
    else:
        form = MoodRecordForm()
    
    return render(request, 'accounts/record_mood.html', {'form': form})

@login_required
def mood_history_view(request):
    """View for displaying user's mood history"""
    mood_records = MoodRecord.objects.filter(user=request.user)
    return render(request, 'accounts/mood_history.html', {'mood_records': mood_records})
