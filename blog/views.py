from django.shortcuts import render
from django.http import HttpResponse
from .models import Post


# Create your views here.

def blog_post(request,title):
    try:
        blog=Post.objects.filter(title=title).first()
        recent_posts = Post.objects.all().order_by('-id')[:3]
        context={'Post': blog,'recent_posts': recent_posts}
        return render(request,'blog/blog_post.html',context)
    except Post.DoesNotExist:
        return HttpResponse("post not found")
    