from django.urls import path
from .views import CartView,OrderView,ApplicationsView

urlpatterns = [
    path('items', CartView.as_view()),
    path('order/', OrderView.as_view()),
    path('applications/', ApplicationsView.as_view(), name='application-list'),
]
