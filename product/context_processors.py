from .models import CustomerAddress

def user_profile(request):
    if request.user.is_authenticated:
        address = CustomerAddress.objects.filter(user=request.user).first()
        return {'address': address}
    return {'address': None}

