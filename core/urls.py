from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.urls import path

app_name = "core"


@login_required
def dashboard(request):
    return HttpResponse("Dashboard")


urlpatterns = [
    path("", dashboard, name="dashboard"),
]
