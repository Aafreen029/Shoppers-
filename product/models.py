from django.db import models
from django.utils.text import slugify
from django.conf import settings
import uuid
from django.utils import timezone
# Create your models here.

class category(models.Model):
    category_name=models.CharField(max_length=50,unique=True)
    cat_image = models.ImageField(upload_to="upload",blank=True,null=True)
    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.category_name
    
class SubCategory(models.Model):
    subcategory_name = models.CharField(max_length=50)
    category = models.ForeignKey(category, on_delete=models.CASCADE, related_name='subcategories')
    slug = models.SlugField(unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            combined = f"{self.subcategory_name}-{self.category.category_name}"
            self.slug = slugify(combined)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.subcategory_name} ({self.category.category_name})"


class colour(models.Model):
    colour_name=models.CharField(max_length=50)

    def __str__(self):
        return self.colour_name

class size(models.Model):
    product_size=models.CharField(max_length=50)

    def __str__(self):
        return self.product_size

class product(models.Model):
    product_name=models.CharField(max_length=50)
    brand = models.CharField(max_length=50, null=True, blank=True)
    description= models.TextField()
    product_price=models.IntegerField()
    discount_price = models.IntegerField(null=True, blank=True)
    thumbnail=models.ImageField(upload_to="upload")
    category_id=models.ForeignKey(category, on_delete=models.CASCADE, null=True)
    sub_cat = models.ForeignKey(SubCategory, on_delete=models.SET_NULL, null=True, blank=True)
    colour_id=models.ManyToManyField(colour)
    size_id=models.ManyToManyField(size)
    product_quantity=models.IntegerField()
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    slug = models.SlugField(unique=True, blank=True,null=True)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
   
    def save(self, *args, **kwargs): 
        if not self.slug:
            self.slug=slugify(self.product_name)
        return super().save(*args, **kwargs)
    
    def __str__(self):
        return self.product_name
    
class ProductCart(models.Model):
    user=models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,null=True, blank=True)
    product_id=models.ForeignKey(product, on_delete=models.CASCADE)
    quantity =models.IntegerField(blank=True, null=True, default=1)
    added_at =models.DateTimeField(auto_now_add=True)
    selected_size = models.ForeignKey(size, on_delete=models.SET_NULL, null=True, blank=True)
    selected_colour = models.ForeignKey(colour, on_delete=models.SET_NULL, null=True, blank=True)
    session_key = models.CharField(max_length=100, null=True, blank=True)
    
    def __str__(self):
         if self.user:
            return self.user.email
         return f"Guest cart ({self.session_key})"

class CustomerAddress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    address_line_1 = models.CharField(max_length=255)
    address_line_2 = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    state = models.CharField(max_length=100)
    country = models.CharField(max_length=100)
    default = models.BooleanField(default=False)
    GENDER_CHOICES = [('male', 'Male'),('female', 'Female'),('other', 'Other'),]
    gender = models.CharField(max_length=10,choices=GENDER_CHOICES,blank=True, null=True)  
    profile_picture = models.ImageField(upload_to='profile_pics', null=True, blank=True,default='profile_pics/default_profile.png')
    height = models.FloatField(null=True, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
class Order(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Confirmed', 'Confirmed'),
        ('Shipped', 'Shipped'),
        ('In Transit', 'In Transit'), 
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),]
    user = models.ForeignKey(settings.AUTH_USER_MODEL,  on_delete=models.CASCADE)
    product = models.ForeignKey('product', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')  
    ordered_at = models.DateTimeField(auto_now_add=True)
    selected_size = models.ForeignKey(size, on_delete=models.SET_NULL, null=True, blank=True)
    selected_colour = models.ForeignKey(colour, on_delete=models.SET_NULL, null=True, blank=True)
    order_id = models.UUIDField(default=uuid.uuid4, editable=False)
    total_paid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    shipping_charge = models.DecimalField(max_digits=10, decimal_places=2, default=0) 
    actual_delivery_date = models.DateTimeField(null=True, blank=True)
    estimated_delivery_date=models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.user.first_name} - {self.product.product_name}"
    
class ProductReview(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    product = models.ForeignKey('product', on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveSmallIntegerField(choices=[(i, str(i)) for i in range(1, 6)])  
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
   

    def __str__(self):
        return f"{self.user.first_name} - {self.product.product_name} - {self.rating}★"
    
class DeliveryAgent(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    phone_number = models.CharField(max_length=15)
    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    assigned_area = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.user} - Agent"

class Delivery(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True)
    agent = models.ForeignKey('DeliveryAgent', on_delete=models.SET_NULL, null=True, blank=True)
    delivery_address = models.ForeignKey(CustomerAddress, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    current_city = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Delivery - Order {self.order.order_id} ({self.order.status})"
    
class Warehouse(models.Model):
    STATE_CHOICES = [
    ('Andhra Pradesh', 'Andhra Pradesh'),
    ('Arunachal Pradesh', 'Arunachal Pradesh'),
    ('Assam', 'Assam'),
    ('Bihar', 'Bihar'),
    ('Chhattisgarh', 'Chhattisgarh'),
    ('Goa', 'Goa'),
    ('Gujarat', 'Gujarat'),
    ('Haryana', 'Haryana'),
    ('Himachal Pradesh', 'Himachal Pradesh'),
    ('Jharkhand', 'Jharkhand'),
    ('Karnataka', 'Karnataka'),
    ('Kerala', 'Kerala'),
    ('Madhya Pradesh', 'Madhya Pradesh'),
    ('Maharashtra', 'Maharashtra'),
    ('Manipur', 'Manipur'),
    ('Meghalaya', 'Meghalaya'),
    ('Mizoram', 'Mizoram'),
    ('Nagaland', 'Nagaland'),
    ('Odisha', 'Odisha'),
    ('Punjab', 'Punjab'),
    ('Rajasthan', 'Rajasthan'),
    ('Sikkim', 'Sikkim'),
    ('Tamil Nadu', 'Tamil Nadu'),
    ('Telangana', 'Telangana'),
    ('Tripura', 'Tripura'),
    ('Uttar Pradesh', 'Uttar Pradesh'),
    ('Uttarakhand', 'Uttarakhand'),
    ('West Bengal', 'West Bengal'),
]

    name = models.CharField(max_length=100)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=20, choices=STATE_CHOICES) 
    address = models.TextField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.city}, {self.state})"

    

