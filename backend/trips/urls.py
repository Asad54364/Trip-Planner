"""URL routes for the trips API."""
from django.urls import path
from . import views

urlpatterns = [
    path('health', views.health_check, name='health-check'),
    path('trips/plan', views.plan_trip_view, name='plan-trip'),
    path('trips/<uuid:trip_id>', views.get_trip, name='get-trip'),
]
