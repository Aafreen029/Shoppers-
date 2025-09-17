
from django.urls import path
from product import views

urlpatterns=[
    path('prod_details/<slug:slug>/',views.product_details,name='product_details'),
    path('recommend-size/<slug:slug>/', views.recommend_size, name='recommend_size'),
    path('add_cart/<int:product_id>/', views.add_cart, name='add_cart'),
    path('remove_cart/<int:product_id>/', views.remove_cart, name='remove_cart'),
    path('update_quantity/<int:product_id>/', views.update_quantity, name='update_quantity'),
    path('cart/',views.view_cart,name='view_cart'),
    path('get_cart_count/',views.getCartCount,name='getCartCount'),
    path('checkout/',views.checkout,name='checkout'),
    path('profile/',views.profile,name='profile'),
    path('address/',views.address,name='address'),
    path('delete_address/',views.delete_address,name='delete_address'),
    path('create-checkout-session/', views.create_checkout_session, name='create_checkout_session'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('order/', views.order, name='order'),
    path('search/', views.search, name='search'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('submit_review',views.submit_review,name='submit_review'),
   
]

    



