from django.db.models.signals import post_save
from django.conf import settings
from django.db import models
from django.db.models import Sum
from django.shortcuts import reverse
from django_countries.fields import CountryField
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

CATEGORY_CHOICES = (
    ('Shirt', 'Shirt'),
    ('Sport wear', 'Sport wear'),
    ('Outwear', 'Outwear')
)

LABEL_CHOICES = (
    ('P', 'primary'),
    ('S', 'secondary'),
    ('D', 'danger')
)

ADDRESS_CHOICES = (
    ('B', 'Billing'),
    ('S', 'Shipping'),
)


class Customer(models.Model):
    user = models.OneToOneField(User, null=True, blank=True, on_delete=models.CASCADE)
    name = models.CharField(max_length=200, null=True, blank=True)
    phone = models.CharField(max_length=200, null=True, blank=True)
    device = models.CharField(max_length=200, null=True, blank=True)

    def __str__(self):
        if self.name:
            name = self.name
        else:
            name = self.device
        return str(name)


class Item(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(blank=True, null=True, max_digits=10, decimal_places=2)
    category = models.CharField(choices=CATEGORY_CHOICES, max_length=20)
    label = models.CharField(choices=LABEL_CHOICES, max_length=1)
    slug = models.SlugField()
    color = models.CharField(max_length=100, default="negro")
    color2 = models.CharField(max_length=100, default="blanco")
    color3 = models.CharField(max_length=100, blank=True, null=True)
    color4 = models.CharField(max_length=100, blank=True, null=True)
    color5 = models.CharField(max_length=100, blank=True, null=True)
    color6 = models.CharField(max_length=100, blank=True, null=True)
    color7 = models.CharField(max_length=100, blank=True, null=True)
    color8 = models.CharField(max_length=100, blank=True, null=True)
    color9 = models.CharField(max_length=100, blank=True, null=True)
    color10 = models.CharField(max_length=100, blank=True, null=True)
    sizeS = models.BooleanField(default=False)
    sizeM = models.BooleanField(default=False)
    sizeL = models.BooleanField(default=False)
    sizeXL = models.BooleanField(default=False)
    description = models.TextField()
    image = models.ImageField()
    image2 = models.ImageField(blank=True, null=True)
    image3 = models.ImageField(blank=True, null=True)
    image4 = models.ImageField(blank=True, null=True)
    image5 = models.ImageField(blank=True, null=True)
    image6 = models.ImageField(blank=True, null=True)
    image7 = models.ImageField(blank=True, null=True)
    image8 = models.ImageField(blank=True, null=True)
    image9 = models.ImageField(blank=True, null=True)
    image10 = models.ImageField(blank=True, null=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("core:product", kwargs={
            'slug': self.slug
        })

    def get_add_to_cart_url(self):
        return reverse("core:add-to-cart", kwargs={
            'slug': self.slug
        })


class OrderItem(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                         on_delete=models.CASCADE)
    # order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    date_added = models.DateTimeField(auto_now_add=True)
    ordered = models.BooleanField(default=False)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    chosenColor = models.CharField(max_length=100, default="")
    chosenSize = models.CharField(max_length=10, default="")

    def __str__(self):
        return f"{self.quantity} de {self.item.title}, {self.chosenColor}, {self.chosenSize}"

    def get_quantity(self):
        return self.quantity

    def get_total_item_price(self):
        return self.quantity * self.item.price

    def get_total_discount_item_price(self):
        return self.quantity * self.item.discount_price

    def get_amount_saved(self):
        return self.get_total_item_price() - self.get_total_discount_item_price()

    def get_final_price(self):
        if self.item.discount_price:
            return self.get_total_discount_item_price()
        return self.get_total_item_price()


class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    # user = models.ForeignKey(settings.AUTH_USER_MODEL,
    #                          on_delete=models.CASCADE)
    ref_code = models.CharField(max_length=20, blank=True, null=True)
    items = models.ManyToManyField(OrderItem)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    ordered = models.BooleanField(default=False)
    department = models.CharField(max_length=100, default="")
    total_order_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    def __str__(self):
        if self.customer.name:
            name = self.customer.name
        else:
            name = self.customer.device
        return str(name)

    def get_total(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_final_price()
        return total

    def get_clothes_number(self):
        number = 0
        for order_item in self.items.all():
            number += order_item.get_quantity()
        return number

    def get_order_items(self):
        return "\n".join([str(item) for item in self.items.all()])


class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100)
    country = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username

    class Meta:
        verbose_name_plural = 'Addresses'


# this class is to show various past project of the company
class Project(models.Model):
    title = models.CharField(max_length=100)
    month = models.CharField(max_length=2, validators=[RegexValidator(r'^\d{1,10}$')])
    year = models.CharField(max_length=4, validators=[RegexValidator(r'^\d{1,10}$')])
    description = models.TextField()
    image = models.ImageField()
    image2 = models.ImageField(blank=True, null=True)
    image3 = models.ImageField(blank=True, null=True)
    image4 = models.ImageField(blank=True, null=True)
    image5 = models.ImageField(blank=True, null=True)
    image6 = models.ImageField(blank=True, null=True)
    image7 = models.ImageField(blank=True, null=True)
    image8 = models.ImageField(blank=True, null=True)
    image9 = models.ImageField(blank=True, null=True)
    image10 = models.ImageField(blank=True, null=True)

    def __str__(self):
        return self.title

