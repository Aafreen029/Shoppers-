from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse
from .models import product,ProductCart,size,colour,CustomerAddress,Order,category,ProductReview, Delivery,ProductReview
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.db.models import Q
from collections import defaultdict
from django.utils.timezone import localtime, now
from uuid import uuid4
from django.contrib import messages
from .utils import validate_image,extract_measurements, recommend_size_upper, recommend_size_pants,get_cart_session_key
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F
from datetime import timedelta
from django.core.files.storage import default_storage
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from django.conf import settings
import json,stripe
stripe.api_key = settings.STRIPE_SECRET_KEY
import os
import mediapipe as mp
import cv2


# Create your views here.
def getCartCount(request):
    if request.user.is_authenticated:
        count = ProductCart.objects.filter(user=request.user).count()
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        count = ProductCart.objects.filter(session_key=session_key, user=None).count()
    return JsonResponse({"count": count})

def product_details(request, slug):
    try:
        prod_details = product.objects.get(slug=slug)
        all_sizes = size.objects.all()
        all_colours = colour.objects.all()
        reviews = ProductReview.objects.filter(product=prod_details).select_related('user').order_by('-created_at')

        for review in reviews:
            review.address = CustomerAddress.objects.filter(user=review.user).first()

        similar_products = product.objects.filter(category_id=prod_details.category_id).exclude(id=prod_details.id)[:4]
        context={"prod_details": prod_details,"all_sizes": all_sizes,"all_colours": all_colours,"reviews":reviews,"similar_products": similar_products}
        return render(request, 'product/product_details.html',context )
    except product.DoesNotExist:
        return HttpResponse("Product not found")
    
def search(request):
    keyword = request.GET.get('keyword', '').strip()
    selected_category_name = request.GET.get('category', '').strip()
    min_price = request.GET.get('min_price',0)
    max_price = request.GET.get('max_price','').strip()
    selected_brands = request.GET.getlist('brand')
    min_rating = request.GET.get('rating')

    # Get the selected category object (if any)
    selected_category_obj = category.objects.filter(Q(category_name__iexact=selected_category_name)).first()

    # Start with annotated products
    products = product.objects.annotate(avg_rating=Avg('productreview__rating'))

    # Apply keyword filter
    if keyword:
        products = products.filter(
            category_id__category_name__icontains=keyword
        ) | product.objects.filter(
            product_name__icontains=keyword
        ) | product.objects.filter(
            description__icontains=keyword
        ) | product.objects.filter(
            brand__icontains=keyword
        )

    # Apply category filter
    if selected_category_obj:
        products = products.filter(category_id=selected_category_obj)

    # Extract brand pool before applying brand/rating/price filters
    brand_pool = products
    brands = sorted(set(p.brand for p in brand_pool if p.brand))

    # Apply brand filter
    if selected_brands:
        products = products.filter(brand__in=selected_brands)

    # Apply rating filter
    if min_rating:
        products = products.filter(avg_rating__gte=int(min_rating))

    # Convert queryset to list for manual price filtering
    products = list(products)

    if min_price:
        products = [p for p in products if (p.discount_price or p.product_price) >= int(min_price)]
    if max_price and str(max_price).isdigit():
        products = [p for p in products if (p.discount_price or p.product_price) <= int(max_price)]

    product_count = len(products)

    # Always show selected category if available
    categories = [selected_category_obj] if selected_category_obj else category.objects.filter(product__in=products).distinct()

    return render(request, 'product/search.html', {
        'products': products,
        'product_count': product_count,
        'categories': categories,
        'selected_category': selected_category_obj,
        'keyword': keyword,
        'selected_brands': selected_brands,
        'brands': brands,
        'min_price': int(min_price) if str(min_price).isdigit() else 0, 
        'max_price': int(max_price) if str(max_price).isdigit() else 30000,
    })

def add_cart(request, product_id):
    try:
        product_obj = product.objects.filter(id=product_id).first()

        if request.method == 'POST':
            if not request.POST.get("size_id") or not request.POST.get("colour_id"):
                messages.error(request, "Please select both size and colour.")
                return redirect("product_details", slug=product_obj.slug)
            
            selected_size_id = request.POST.get('size_id')
            selected_colour_id = request.POST.get('colour_id')
            buy_now = request.POST.get('buy_now') == 'true'
            size_obj = size.objects.get(id=selected_size_id) if selected_size_id else None
            colour_obj = colour.objects.get(id=selected_colour_id) if selected_colour_id else None

            if request.user.is_authenticated:
                cart_item, created = ProductCart.objects.get_or_create(
                    product_id=product_obj,
                    user=request.user,
                    selected_size=size_obj,
                    selected_colour=colour_obj
                )
            else:
                session_key = get_cart_session_key(request)
                cart_item, created = ProductCart.objects.get_or_create(product_id=product_obj,session_key=session_key,selected_size=size_obj,selected_colour=colour_obj)

            if buy_now:
                return redirect('/checkout/')
            else:
                return redirect('/cart/')
        else:
            return HttpResponse("product not added")
    except Exception as e:
        return HttpResponse(f"Error adding product to cart: {str(e)}", status=500)

def view_cart(request):
    context = {}
    try:
        if request.user.is_authenticated:
            cart_items = ProductCart.objects.filter(user=request.user)
        else:
            session_key = get_cart_session_key(request)
            cart_items = ProductCart.objects.filter(session_key=session_key)

        count = cart_items.count()
        #total_price = sum(item.product_id.discount_price or item.product_id.product_price * item.quantity for item in cart_items)
        total_price = 0
        for item in cart_items:
            unit_price = item.product_id.discount_price if item.product_id.discount_price else item.product_id.product_price
            total_price += unit_price * item.quantity
        shipping_charge = 40
        grand_total = total_price + shipping_charge

        context = {'cart_items': cart_items,'total_price': total_price,'shipping_charge': shipping_charge,'grand_total': grand_total,'cart_item_count': count}
        return render(request, 'product/add_cart.html', context)
    except Exception as e:
        return HttpResponse(f"Error loading cart: {str(e)}", status=500)
    
@csrf_exempt
def update_quantity(request, product_id):
    try:
        if request.method != 'POST':
            return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=405)

        product_obj = product.objects.filter(id=product_id).first()
        if not product_obj:
            return JsonResponse({'success': False, 'message': 'Product not found'}, status=404)

        session_key = get_cart_session_key(request)
        data = json.loads(request.body)
        action = data.get('action')
        size_id = data.get('size_id')
        colour_id = data.get('colour_id')

        if request.user.is_authenticated:
            cart_item = ProductCart.objects.get(product_id=product_obj,user=request.user,selected_size_id=size_id,selected_colour_id=colour_id)
            cart_items = ProductCart.objects.filter(user=request.user)
        else:
            cart_item = ProductCart.objects.get(product_id=product_obj,session_key=session_key,selected_size_id=size_id,selected_colour_id=colour_id)
            cart_items = ProductCart.objects.filter(session_key=session_key)

        if action == 'increase':
            cart_item.quantity += 1
        elif action == 'decrease' and cart_item.quantity > 1:
            cart_item.quantity -= 1
        else:
            return JsonResponse({'success': False, 'message': 'Invalid action or quantity'}, status=400)
        cart_item.save()

        #item_total = cart_item.product_id.discount_price or cart_item.product_id.product_price * cart_item.quantity
        #total_price = sum(item.product_id.discount_price or item.product_id.product_price * item.quantity for item in cart_items)
        unit_price = cart_item.product_id.discount_price if cart_item.product_id.discount_price else cart_item.product_id.product_price
        item_total = unit_price * cart_item.quantity
        total_price = sum(
            (item.product_id.discount_price if item.product_id.discount_price else item.product_id.product_price) * item.quantity
            for item in cart_items)
        shipping_charge = 40
        grand_total = total_price + shipping_charge

        return JsonResponse({'success': True,'quantity': cart_item.quantity,'item_total': item_total,'total_price': total_price,'shipping_charge': shipping_charge,'grand_total': grand_total})

    except ProductCart.DoesNotExist:
        return JsonResponse({'success': False, 'message': 'Cart item not found'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)  

def remove_cart(request, product_id):
    try:
        session_key = get_cart_session_key(request)
        if request.user.is_authenticated:
            cart_item = ProductCart.objects.filter(product_id__id=product_id, user=request.user).first()
        else:
            cart_item = ProductCart.objects.filter(product_id__id=product_id, session_key=session_key).first()

        if cart_item:
            cart_item.delete()
        return redirect('/cart/')
    except Exception as e:
        return HttpResponse(f"Error removing product from cart: {str(e)}", status=500)
    
def checkout(request):
    user = request.user
    session_key = get_cart_session_key(request)
    new_address = False
    edit_address_id = None
    address_to_edit = None
    show_all_addresses = False

    if request.user.is_authenticated:
        addresses = CustomerAddress.objects.filter(user=user)
    else:
        addresses = None  

    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect('login') 

        if request.POST.get('add_address') == 'true':
            new_address = True

        elif request.POST.get('edit_address_id'):
            edit_address_id = request.POST.get('edit_address_id')
            address_to_edit = get_object_or_404(CustomerAddress, id=edit_address_id, user=user)
            new_address = True

        elif request.POST.get('delete_address') == 'true':
            address_id = request.POST.get('address_id')
            address = get_object_or_404(CustomerAddress, id=address_id, user=user)
            address.delete()
            return redirect('checkout')

        elif request.POST.get('set_default') == 'true':
            address_id = request.POST.get('address_id')
            if address_id:
                CustomerAddress.objects.filter(user=user, default=True).update(default=False)
                try:
                    new_default = CustomerAddress.objects.get(id=address_id, user=user)
                    new_default.default = True
                    new_default.save()
                except CustomerAddress.DoesNotExist:
                    pass
            show_all_addresses = False
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True})
            return redirect('checkout')
        
        elif request.POST.get('change_address') == 'true':
            show_all_addresses = True

        else:
            address_id = request.POST.get('address_id')
            if address_id:
                address = get_object_or_404(CustomerAddress, id=address_id, user=user)
                address.first_name = request.POST.get('first_name')
                address.last_name = request.POST.get('last_name')
                address.email = request.POST.get('email')
                address.phone = request.POST.get('phone')
                address.address_line_1 = request.POST.get('address_line_1')
                address.address_line_2 = request.POST.get('address_line_2')
                address.city = request.POST.get('city')
                address.pincode = request.POST.get('pincode')
                address.state = request.POST.get('state')
                address.country = request.POST.get('country')
                address.save()
            else:
                existing_default = CustomerAddress.objects.filter(user=user, default=True).first()
                if existing_default:
                    existing_default.default = False
                    existing_default.save()  

                CustomerAddress.objects.create(
                    user=user,
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    address_line_1=request.POST.get('address_line_1'),
                    address_line_2=request.POST.get('address_line_2'),
                    city=request.POST.get('city'),
                    pincode=request.POST.get('pincode'),
                    state=request.POST.get('state'),
                    country=request.POST.get('country'),
                    default=True,
                )
            return redirect('checkout')

    if request.user.is_authenticated:
        cart_items = ProductCart.objects.filter(user=user)
    else:
        cart_items = ProductCart.objects.filter(session_key=session_key)
    total_items = sum(item.quantity for item in cart_items)
    total_price = 0
    for item in cart_items:
            unit_price = item.product_id.discount_price if item.product_id.discount_price else item.product_id.product_price
            total_price += unit_price * item.quantity
    shipping_charge = 40
    grand_total = total_price + shipping_charge
    addresses_to_show = addresses.filter(default=True) if (request.user.is_authenticated and not show_all_addresses) else addresses
    context = {
        'addresses_to_show': addresses_to_show,
        'addresses': addresses,
        'new_address': new_address,
        'address_to_edit': address_to_edit,
        'total_price': total_price,
        'shipping_charge': shipping_charge,
        'grand_total': grand_total,
        'cart_items': cart_items,
        'total_items':total_items,
        'STRIPE_PUBLIC_KEY': settings.STRIPE_PUBLIC_KEY,
    }
    return render(request, 'product/checkout.html', context)

@login_required(login_url='login')
def profile(request):
    user = request.user
    address = CustomerAddress.objects.filter(user=user).first()
    profile_exists = bool(address)
    edit_mode = False
    gender_choices = ['female', 'male', 'other']

    if request.method == 'POST':
        if request.POST.get('edit_profile') == 'true':
            edit_mode = True
        else:
            profile_picture = request.FILES.get('profile_picture')
            remove_picture = request.POST.get('remove_profile_picture')

            if not profile_exists:
                address = CustomerAddress.objects.create(
                    user=user,
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    gender=request.POST.get('gender'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    profile_picture=profile_picture if profile_picture else 'profile_pics/default_profile.png'
                )
            else:
                address.first_name = request.POST.get('first_name')
                address.last_name = request.POST.get('last_name')
                address.gender = request.POST.get('gender')
                address.email = request.POST.get('email')
                address.phone = request.POST.get('phone')

                if remove_picture == 'on':
                    if address.profile_picture and address.profile_picture.name != 'profile_pics/default_profile.png':
                        address.profile_picture.delete(save=False)
                    address.profile_picture = 'profile_pics/default_profile.png'
                elif profile_picture:
                    address.profile_picture = profile_picture
                address.save()
            return redirect('profile')
        
    context = {'profile_exists': profile_exists,'address': address,'edit_mode': edit_mode,'gender_choices': gender_choices}
    return render(request, 'product/profile.html', context)

def address(request):
    user = request.user
    addresses = CustomerAddress.objects.filter(user=user)
    new_address = False
    edit_address_id = None
    address_to_edit = None

    if request.method == 'POST':
        if request.POST.get('add_address') == 'true':
            new_address = True

        elif request.POST.get('edit_address_id'):
            edit_address_id = request.POST.get('edit_address_id')
            address_to_edit = get_object_or_404(CustomerAddress, id=edit_address_id, user=user)
            new_address = True

        elif request.POST.get('set_default') == 'true':
            address_id = request.POST.get('address_id')
            if address_id:
                CustomerAddress.objects.filter(user=user, default=True).update(default=False)
                try:
                    new_default = CustomerAddress.objects.get(id=address_id, user=user)
                    new_default.default = True
                    new_default.save()
                except CustomerAddress.DoesNotExist:
                    pass
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return HttpResponse(status=204)
            return redirect('address')
        else:
            address_id = request.POST.get('address_id')
            if address_id:
                address = get_object_or_404(CustomerAddress, id=address_id, user=user)
                address.first_name = request.POST.get('first_name')
                address.last_name = request.POST.get('last_name')
                address.email = request.POST.get('email')
                address.phone = request.POST.get('phone')
                address.address_line_1 = request.POST.get('address_line_1')
                address.address_line_2 = request.POST.get('address_line_2')
                address.city = request.POST.get('city')
                address.pincode = request.POST.get('pincode')
                address.state = request.POST.get('state')
                address.country = request.POST.get('country')
                address.save()
            else:
                existing_default = CustomerAddress.objects.filter(user=user, default=True).first()
                if existing_default:
                    existing_default.default = False
                    existing_default.save()

                CustomerAddress.objects.create(
                    user=user,
                    first_name=request.POST.get('first_name'),
                    last_name=request.POST.get('last_name'),
                    email=request.POST.get('email'),
                    phone=request.POST.get('phone'),
                    address_line_1=request.POST.get('address_line_1'),
                    address_line_2=request.POST.get('address_line_2'),
                    city=request.POST.get('city'),
                    pincode=request.POST.get('pincode'),
                    state=request.POST.get('state'),
                    country=request.POST.get('country'),
                    default=True
                )
            return redirect('address')
    context = {'new_address': new_address,'addresses': addresses,'address_to_edit': address_to_edit}
    return render(request, 'product/address.html', context)

def delete_address(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')
        address = get_object_or_404(CustomerAddress, id=address_id, user=request.user)
        address.delete()
    return redirect('address')

@login_required(login_url='login')
def create_checkout_session(request):
    user = request.user
    cart_items = ProductCart.objects.filter(user=user)
    line_items = []
    total_price = 0

    for item in cart_items:
       
        unit_price = item.product_id.discount_price if item.product_id.discount_price else item.product_id.product_price
        
       
        item_total = unit_price * item.quantity
        total_price += item_total

       
        line_items.append({
            'price_data': {
                'currency': 'inr',
                'product_data': {
                    'name': item.product_id.product_name,
                },
                'unit_amount': int(unit_price * 100), 
            },
            'quantity': item.quantity,
        })

  
    shipping_charge = 40
    grand_total = total_price + shipping_charge

  
    line_items.append({
        'price_data': {
            'currency': 'inr',
            'product_data': {
                'name': 'Shipping Charge',
            },
            'unit_amount': int(shipping_charge * 100), 
        },
        'quantity': 1,
    })

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=line_items,
            mode='payment',
            customer_email=user.email,
            success_url=request.build_absolute_uri('/payment-success/'),
            cancel_url=request.build_absolute_uri('/cart/'),
        )
        return JsonResponse({
            'id': checkout_session.id,
            'grand_total': grand_total  
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

def add_business_days(start_date, days):
    current_date = start_date
    added_days = 0
    while added_days < days:
        current_date += timedelta(days=1)
        if current_date.weekday() < 5: 
            added_days += 1
    return current_date

def payment_success(request):
    user = request.user
    cart_items = ProductCart.objects.filter(user=user)

    if not cart_items:
        return redirect('order')

    total_product_price = sum(
        (item.product_id.discount_price if item.product_id.discount_price else item.product_id.product_price) * item.quantity
        for item in cart_items
    )

    shipping_charge = 40
    order_uuid = uuid4()

    for item in cart_items:
        product = item.product_id
        unit_price = product.discount_price if product.discount_price else product.product_price
        price = unit_price * item.quantity

        # Proportional shipping for this item
        proportional_shipping = (price / total_product_price) * shipping_charge if total_product_price else 0
        total_paid = price + proportional_shipping

        # Decrease stock
        if product.product_quantity >= item.quantity:
            product.product_quantity -= item.quantity
            product.save()
        else:
            messages.error(request, f"Insufficient quantity for {product.product_name}")
            return redirect('order')

        # Estimated delivery date
        estimated_delivery = add_business_days(now().date(), 5)

        # Save order
        Order.objects.create(
            user=user,
            product=product,
            quantity=item.quantity,
            price=price,
            shipping_charge=proportional_shipping,
            total_paid=total_paid,
            selected_size=item.selected_size,
            selected_colour=item.selected_colour,
            order_id=order_uuid,
            estimated_delivery_date=estimated_delivery,
        )

    cart_items.delete()
    return render(request, 'product/payment_success.html')

def order(request):
    user = request.user
    orders = Order.objects.filter(user=user).order_by('-ordered_at')
    grouped_orders = defaultdict(list)
    order_timestamps = {}

    for order_item in orders:
        grouped_orders[order_item.order_id].append(order_item)
        order_timestamps[order_item.order_id] = localtime(order_item.ordered_at)
        review = ProductReview.objects.filter(user=user,product=order_item.product,order=order_item).first()
        order_item.review_submitted = bool(review)
        order_item.user_review = review 
        delivery = Delivery.objects.filter(order=order_item).first()
        order_item.delivery = delivery
        
    sorted_grouped_orders = sorted(
        grouped_orders.items(),
        key=lambda x: order_timestamps[x[0]],
        reverse=True )
    
    context = {'grouped_orders': sorted_grouped_orders, 'address': CustomerAddress.objects.filter(user=user).first()}
    return render(request, 'product/order.html', context)

def cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id, user=request.user)

        if order.status == 'Pending':
            order.status = 'Cancelled'
            order.save()

            product = order.product
            product.product_quantity += order.quantity
            product.save()

            messages.success(request, "Order cancelled successfully.")
        else:
            messages.error(request, "Only pending orders can be cancelled.")
    except Order.DoesNotExist:
        messages.error(request, "Order not found.")
    return redirect('order')

def submit_review(request):
    if request.method == "POST":
        user = request.user
        product_id = request.POST.get("product_id")
        order_id = request.POST.get("order_id")
        rating = request.POST.get("rating")
        review = request.POST.get("review")

        if not all([product_id, order_id, rating]):
            messages.error(request, "Incomplete review data.")
            return redirect('order')
        try:
            product_obj = product.objects.get(id=product_id)
            order_obj = Order.objects.get(id=order_id)
        except (product.DoesNotExist, Order.DoesNotExist):
            messages.error(request, "Invalid product or order.")
            return redirect('order')
        
        if order_obj.user != user or order_obj.status != "Delivered":
            messages.error(request, "You can only review delivered products.")
            return redirect('order')
        
        existing_review = ProductReview.objects.filter(user=user,product=product_obj,order=order_obj).first()
        if existing_review:
            existing_review.rating = rating
            existing_review.review = review
            existing_review.save()
            messages.success(request, "Your review has been updated.")
        else:
            ProductReview.objects.create(user=user,product=product_obj,order=order_obj,rating=rating,review=review,)
            messages.success(request, "Thank you for your review!")
    return redirect('order')

def recommend_size(request, slug):
    if request.method == "POST":
        image_file = request.FILES.get('user_image')
        user_height = request.POST.get('user_height')

        if not image_file or not user_height:
            messages.error(request, "Please upload an image and enter your height.")
            return redirect('product_details', slug=slug)

        try:
            user_height = float(user_height)
        except ValueError:
            messages.error(request, "Invalid height format.")
            return redirect('product_details', slug=slug)

        image_path = default_storage.save('temp/' + image_file.name, image_file)
        image_path = default_storage.path(image_path)

        try:
            # Load image and run MediaPipe Holistic with WorldLandmark
            
            image_rgb = validate_image(image_path)
            

            with mp.solutions.holistic.Holistic(static_image_mode=True, model_complexity=2) as holistic:
                results = holistic.process(image_rgb)
            
            if not results.pose_world_landmarks:
                messages.error(request, "Could not detect pose landmarks. Please try a clearer image.")
                return redirect('product_details', slug=slug)
            measurements = extract_measurements(results, user_height)
            if measurements['accuracy_score'] < 0.7:
                messages.warning(request, f"Pose accuracy too low ({measurements['accuracy_score']*100:.1f}%). Please upload a clearer image.")
                return redirect('product_details', slug=slug)
            
            print("\n Extracted Measurements:")
            for key, value in measurements.items():
                print(f"{key}: {value:.2f} cm")

            # Recommend sizes
            top_size = recommend_size_upper(
                measurements['shoulder'],
                measurements['chest']
            )
            bottom_size = recommend_size_pants(
                measurements['waist'],
                measurements['inseam']
            )

            prod_details = product.objects.get(slug=slug)
            all_sizes = size.objects.all()
            all_colours = colour.objects.all()
            similar_products = product.objects.filter(category_id=prod_details.category_id.id).exclude(id=prod_details.id)[:4]

            context = {
                "prod_details": prod_details,
                "accuracy_score": measurements['accuracy_score'] * 100,
                "recommended_size_top": top_size,
                "recommended_size_bottom" : bottom_size,
                "all_sizes": all_sizes,
                "all_colours": all_colours,
                "similar_products": similar_products
               
            }
            return render(request, 'product/product_details.html', context)

        except Exception as e:
            messages.error(request, f"Error during size recommendation: {str(e)}")
            return redirect('product_details', slug=slug)

        finally:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)

    return redirect('product_details', slug=slug)








    




 




