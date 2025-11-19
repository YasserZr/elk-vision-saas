from django.urls import path
from . import views

urlpatterns = [
    path('', views.AlertListView.as_view(), name='alert-list'),
]
