from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Attendance
from django.utils import timezone

@login_required
def mark_attendance(request):
    if request.method == 'POST':
        type = request.POST.get('type')
        now = timezone.now()
        Attendance.objects.create(user=request.user, date=now.date(), time=now.time(), type=type)
        return redirect('attendance_list')
    return render(request, 'attendance/mark.html')

@login_required
def attendance_list(request):
    attendances = Attendance.objects.filter(user=request.user).order_by('-date', '-time')
    return render(request, 'attendance/list.html', {'attendances': attendances})
