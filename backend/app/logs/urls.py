from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.LogSearchView.as_view(), name='log-search'),
]
