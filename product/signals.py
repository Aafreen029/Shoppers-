from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Order, Delivery

@receiver(pre_save, sender=Order)
def update_delivery_on_status_change(sender, instance, **kwargs):
    if not instance.pk:
        return  

    try:
        old_order = Order.objects.get(pk=instance.pk)
    except Order.DoesNotExist:
        return
    if old_order.status != 'Delivered' and instance.status == 'Delivered':
        instance.actual_delivery_date = timezone.now()
        try:
            delivery = Delivery.objects.get(order=instance)
            delivery.delivered_at = timezone.now()
            delivery.save()
        except Delivery.DoesNotExist:
            pass
