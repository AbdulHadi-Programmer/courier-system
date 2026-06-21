from django.urls import path

from . import views

app_name = 'shipments'

urlpatterns = [
    path('create/', views.shipment_create, name='create'),
    path('', views.shipment_list, name='list'),
    path('<int:pk>/', views.shipment_detail, name='detail'),
    path('<int:pk>/cancel/', views.shipment_cancel, name='cancel'),
    path('<int:pk>/update-status/', views.shipment_update_status, name='update_status'),
    path('<int:pk>/return/', views.shipment_return, name='return_shipment'),
]
