from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from complaints.models import Complaint
from reports.models import Report


@login_required
def home(request):
    total_complaints = Complaint.objects.count()
    total_reports = Report.objects.count()
    user_name = request.user.get_full_name() or request.user.username
    return render(
        request,
        "home.html",
        {
            "total_complaints": total_complaints,
            "total_reports": total_reports,
            "user_name": user_name,
        },
    )
