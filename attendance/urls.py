from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.attendance_list, name='attendance_list'),
    path('select/<str:person_type>/', views.select_person_type, name='select_person_type'),
    path('report/<str:person_type>/<str:identificacion>/', views.select_month, name='select_month'),
]