from django.shortcuts import render,redirect
from django.contrib.auth import get_user_model,login,authenticate,logout
from django.contrib import messages
from home.models import CustomUser
from product.models import ProductCart 
from product.utils import get_cart_session_key 
from .helpers import send_forget_password_mail
from .models import Profile
import uuid
User=get_user_model()

def signup(request):
     if request.method == 'POST':
   
       fullname=request.POST['fullname']
       email=request.POST['email']
       phone_number=request.POST['phone_number']
       password=request.POST['password']
       confirm_password=request.POST['confirm_password']

       if password != confirm_password:
           messages.error(request,"password do not match")
           return redirect('/user/signup/')
       
       if CustomUser.objects.filter(email=email).exists():
           messages.error(request," Email already Registerd")
           return redirect('/user/signup/')
       
       #email_username=email.split('@')[0]
       
       myuser=CustomUser.objects.create_user(email=email,phone_number=phone_number,password=password,username=email)
       myuser.first_name=fullname
      
       messages.success(request,"Account created successfully")
       return redirect('/user/signup/')
     else:
         return render(request,'auth/signup.html')


def loginViews(request):
    if request.method == 'POST':
        email1 = request.POST.get('email1')
        password = request.POST.get('password')

        try:
            user_obj = CustomUser.objects.get(email=email1)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Invalid email or password')
            return redirect('/user/login/')

        user = authenticate(request, email=email1, password=password)

        if user is not None:
            session_key = get_cart_session_key(request)
            login(request, user)
            messages.success(request, 'Successfully logged in!')
            guest_cart_items = ProductCart.objects.filter(user__isnull=True, session_key=session_key)

            for item in guest_cart_items:
               
                existing_item = ProductCart.objects.filter(
                    user=user,
                    product_id=item.product_id,
                    selected_size=item.selected_size,
                    selected_colour=item.selected_colour
                ).first()

                if existing_item:
                    existing_item.quantity += item.quantity
                    existing_item.save()
                    item.delete()
                else:
                    item.user = user
                    item.session_key = None
                    item.save()

            return redirect('/')  
        else:
            messages.error(request, 'Invalid email or password')

    return render(request, 'auth/login.html')

def logoutViews(request):
    logout(request)
    messages.error(request, "Successfully logged out")
    return redirect('/')

def ForgetPassword(request):
    try:
        if request.method == 'POST':
            username=request.POST.get('username')
            print(username,"hellooo")

            if not User.objects.filter(username=username).first():
                messages.success(request,'Not user found with this username')
                return redirect('forget-password')
            
            user_obj=User.objects.get(username=username)
            print(user_obj,"54545454")
            token= str(uuid.uuid4())
            #profile_obj=Profile.objects.get(user = user_obj)
            profile_obj, created = Profile.objects.get_or_create(user=user_obj)
            profile_obj.forget_password_token= token
            profile_obj.save()
            send_forget_password_mail(user_obj.email,token)
            messages.success(request,'An email is sent')
            return redirect('forget-password')

    except Exception as e:
        print(e)
    return render(request,'auth/forget-password.html')

def ChangePassword(request,token):
        context={}
        try:
            profile_obj=Profile.objects.filter(forget_password_token=token).first()
            print(profile_obj.user)
           
            if request.method == 'POST':
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('reconfirm_password')

            
                if  new_password != confirm_password:
                 messages.success(request, 'both should  be equal.')
                 return redirect(f'/change-password/{token}/')
                         
            
                user_obj = User.objects.get(id = profile_obj.user.id)
                user_obj.set_password(new_password)
                user_obj.save()
                messages.success(request, "Password updated successfully!")
                return redirect('/user/login/')
            return render(request,'auth/change-password.html',context)
            
              
        except Exception as e:
         print(e)
         return render(request,'auth/change-password.html',context)
