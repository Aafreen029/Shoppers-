from django.contrib import admin
from .models import category,SubCategory,colour,size,product, ProductCart,CustomerAddress,Order,ProductReview,DeliveryAgent,Delivery,Warehouse
from django.contrib import admin
from .models import Order

# Register your models here.
admin.site.register(category)
admin.site.register(SubCategory)
admin.site.register(colour)
admin.site.register(size)
admin.site.register(product)
admin.site.register(ProductCart)
admin.site.register(CustomerAddress)
admin.site.register(ProductReview)
admin.site.register(DeliveryAgent)
admin.site.register(Delivery)
admin.site.register(Warehouse)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['user', 'product', 'status', 'ordered_at']
    readonly_fields = ['actual_delivery_date', 'order_id']

    def get_readonly_fields(self, request, obj=None):
        readonly = list(super().get_readonly_fields(request, obj))
        
        if not request.user.is_superuser:
            readonly.append('status')  
        return readonly

admin.site.register(Order,OrderAdmin)
