from django.shortcuts import render
from django.contrib.auth import get_user_model
from blog.models import Post
from product.models import product,category
from django.core.paginator import Paginator

User=get_user_model()

# Create your views here.
'''def home(request):
    products=product.objects.all()
    allposts=Post.objects.all()
    paginator = Paginator(allposts, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context={'products': products,'allposts': allposts,'page_obj': page_obj}
    return render(request,'index.html', context)'''


def home(request):
    
    categories = category.objects.all()

    
    products_by_category = {}
    for cat in categories:
        products_by_category[cat] = product.objects.filter(category_id=cat)

    allposts = Post.objects.all()
    paginator = Paginator(allposts, 4)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'products_by_category': products_by_category,
        'categories': categories,
        'page_obj': page_obj
    }
    return render(request, 'index.html', context)




