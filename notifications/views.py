from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from .models import Notification

@login_required
def notification_list(request):
    notifs = request.user.notifications.all()
    notifs.filter(is_read=False).update(is_read=True)
    return render(request, 'notifications/list.html', {'notifications': notifs})

@login_required
def mark_read(request, pk):
    n = get_object_or_404(Notification, pk=pk, user=request.user)
    n.is_read = True; n.save()
    return JsonResponse({'ok': True})

@login_required
def unread_count(request):
    count = request.user.notifications.filter(is_read=False).count()
    return JsonResponse({'count': count})
