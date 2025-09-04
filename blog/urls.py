from django.urls import path
from blog import views

urlpatterns=[
   
    path('blog/<str:title>/',views.blog_post,name='blog_post'),
]