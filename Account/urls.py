
from django.urls import path
from account import views

urlpatterns=[
    path('signup/',views.signup,name='signup'),
    path('login/',views.loginViews,name='login'),
    path('logout/',views.logoutViews,name='logout'),
    path('forget-password/',views.ForgetPassword,name='forget_password'),
    path('change-password/<token>/',views.ChangePassword,name='change_password'),
]