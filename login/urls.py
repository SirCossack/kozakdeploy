from django.urls import path
from . import views

urlpatterns = [
    path('', views.logged_in, name='home'),
    path('accounts/profile/', views.logged_in),
    path('accounts/login/', views.logged_in),
    path('commands/', views.add_command),
    path('commands/delete/', views.delete_command),
    path('commands/adding/', views.add_command_form),
    path('log-out', views.log_out, name='logout'),
    path('activate-bot', views.activate_bot, name='activatebot'),
    path('variables/', views.add_variable, name='addvar'),
    path('variables/delete/', views.delete_variable),
    path('variables/adding/', views.add_variable_form),
    path('click/', views.wtfisclick, name='click')

]