
from decimal import Decimal
from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
from base.emails import send_account_activation_email
from products.models import Product, SizeVariant, ColorVariant

class Profile(BaseModel):
    user = models.OneToOneField(User , on_delete=models.CASCADE , related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100 , null=True , blank=True)
    profile_image = models.ImageField(upload_to = 'profile')

    def get_cart_count(self):
        return CartItems.objects.filter(cart__is_paid=False, cart__user=self.user).count()

class Cart(BaseModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts')
    is_paid = models.BooleanField(default=False)

    def get_cart_total(self):
        cart_items = self.cart_items.all()
        total_price = Decimal('0.00')
        print(cart_items)
        for cart_item in cart_items:
            product_price = Decimal(str(cart_item.size_variant.price))
            print(product_price)
            total_price += product_price
            print(total_price)

            if hasattr(cart_item, 'quantity'):
                quantity = int(cart_item.quantity)  # Assuming quantity is an integer
                if quantity > 1:
                    total_price = product_price * quantity

        return total_price


class CartItems(BaseModel):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='cart_items')
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)
    color_variant = models.ForeignKey(ColorVariant, on_delete=models.SET_NULL, null=True, blank=True)
    size_variant = models.ForeignKey(SizeVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)

    def get_product_price(self):
        price = []

        if self.size_variant:
            size_variant_price = self.size_variant.price
            price.append(size_variant_price)
        else:
            price.append(self.product.price)

        return sum(price)

@receiver(post_save , sender = User)
def  send_email_token(sender , instance , created , **kwargs):
    try:
        if created:
            email_token = str(uuid.uuid4())
            Profile.objects.create(user = instance , email_token = email_token)
            email = instance.email
            send_account_activation_email(email , email_token)

    except Exception as e:
        print(e)

