from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.dashboard_view, name='dashboard'),
    path('create-account/', views.create_account_view, name='create_account'),
    path('deposit/', views.deposit_view, name='deposit'),
    path('withdraw/', views.withdraw_view, name='withdraw'),
    path('history/', views.transaction_history_view, name='history'),
]
