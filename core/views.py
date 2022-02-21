import random
import string

import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import RegexValidator
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View
from django.http import HttpResponseRedirect

from .forms import CheckoutForm, OrderItemForm
from .models import Item, OrderItem, Order, Customer

from django.contrib import auth

#stripe.api_key = settings.STRIPE_SECRET_KEY

CATEGORY_CHOICES = (
    ('Shirt', 'Shirt'),
    ('Sport wear', 'Sport wear'),
    ('Outwear', 'Outwear')
)

DEPARTMENT_PRICES = (
    ('Beni', 50),
    ('Chuquisaca', 30),
    ('Cochabamba', 0),
    ('La Paz', 60),
    ('Oruro', 40),
    ('Pando', 30),
    ('Potosí', 35),
    ('Santa Cruz', 20),
    ('Tarija', 40)
)


def create_ref_code():
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=20))


def products(request):
    context = {
        'items': Item.objects.all()
    }
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == '':
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            form = CheckoutForm(initial={'chosen_department': 'Cochabamba'})
            department_prices = DEPARTMENT_PRICES

            """try:
                customer = self.request.user.customer
            except:"""
            device = self.request.COOKIES['device']
            customer_qs = Customer.objects.filter(device=device)

            if customer_qs.exists():
                customer = Customer.objects.filter(device=device).first()
            else:
                customer = Customer.objects.create(device=device)

            order_qs = Order.objects.filter(customer=customer, ordered=False)

            if order_qs.exists():
                order = Order.objects.get(customer=customer, ordered=False)
            else:
                order = None

            context = {
                'form': form,
                'order': order,
                'department_prices': department_prices,
            }

            return render(self.request, "checkout.html", context)

        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
        return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            try:
                device = self.request.COOKIES['device']
                customer_qs = Customer.objects.filter(device=device)

                if customer_qs.exists():
                    customer = Customer.objects.filter(device=device).first()
                else:
                    customer = Customer.objects.create(device=device)

                order = Order.objects.get(customer=customer, ordered=False)
                if form.is_valid():
                    chosen_department = form.cleaned_data.get('chosen_department')
                    nombre = form.cleaned_data.get('nombre')
                    apellido = form.cleaned_data.get('apellido')
                    phoneNumber = form.cleaned_data.get('phoneNumber')

                    name = str(nombre) + ' ' + str(apellido)
                    phoneNumberRegex = RegexValidator(regex=r"^\+?1?\d{8,15}$")
                    phoneNumberRegex(phoneNumber)

                    # check if customer with same device and name and phone number already exists
                    # if not, create a new one
                    customer_check = Customer.objects.filter(device=device, name=name, phone=phoneNumber)

                    if customer_check.exists():
                        new_customer = Customer.objects.get(device=device, name=name, phoneNumber=phoneNumber)
                    else:
                        new_customer = Customer()
                        new_customer.name = name
                        new_customer.phone = phoneNumber
                        new_customer.device = device
                        new_customer.save()

                    # set order and the items as ordered, create ref_code and set customer
                    # for searching the order 'customer' is enough, because only device number is important
                    order_qs = Order.objects.filter(customer=customer, ordered=False)

                    if order_qs.exists():
                        order = order_qs[0]

                    order_items = order.items.all()
                    order_items.update(ordered=True, customer=new_customer)
                    for item in order_items:
                        item.save()

                    order.ordered = True
                    order.ref_code = create_ref_code()
                    order.customer = new_customer
                    order.department = chosen_department
                    for name, value in DEPARTMENT_PRICES:
                        if name == chosen_department:
                            shipping_price = value
                    order.total_order_price = order.get_total() + shipping_price
                    order.save()

                    messages.info(self.request, "Solo para testing!!!")
                    wpp_string = ""
                    for item in order_items:
                        wpp_string += f"%0A{item.quantity}%20x%20{item.item.title},%20talla:%20{item.chosenSize},%20color:%20{item.chosenColor}"
                    url = f"https://wa.me/59173185605?text=Hola%20Ojos%20de%20Selva%2C%0AQuiero%20pedir%20por%20favor{wpp_string}%0Aen%20color%20rojo%20de%20talla%20L.%0AMuchas%20gracias!"
                    # return redirect('https://wa.me/59173185605?text=Hola%20Ojos%20de%20Selva%2C%0AQuiero%20pedir%20por%20favor%20una%20polera%20de%20navidad%20en%20color%20rojo%20de%20talla%20L.%0AMuchas%20gracias!')
                    # return redirect('https://wa.me/59173185605?text=Hola%20Ojos%20de%20Selva%2C%0AQuiero%20pedir%20por%20favor%20una%20polera%20de%20navidad%20en%20color%20rojo%20de%20talla%20L.%0AMuchas%20gracias!'+order.department)
                    return redirect(url)

                else:
                    messages.info(self.request, "Por favor llene todos los campos.")

            except ObjectDoesNotExist:
                print('object does not exist')
                messages.warning(self.request, "No tiene un pedido activo.")
            return redirect("core:checkout")

        except ValidationError:
            print('phone number')
            messages.info(self.request, "Por favor ingrese un número de teléfono válido.")
        return redirect("core:checkout")


class HomeView(ListView):
    # model = Item
    paginate_by = 10
    # ordering = ['title']
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        category_list = []
        for name, value in CATEGORY_CHOICES:
            for item in Item.objects.all():
                if item.category == value and not value in category_list:
                    category_list.append(value)

        object_list = Item.objects.all().order_by('title')

        device = self.request.COOKIES['device']
        customer_qs = Customer.objects.filter(device=device)

        if customer_qs.exists():
            customer = Customer.objects.filter(device=device).first()
        else:
            customer = Customer.objects.create(device=device)

        order_qs = Order.objects.filter(customer=customer, ordered=False)

        if order_qs.exists():
            order = Order.objects.get(customer=customer, ordered=False)
        else:
            order = None

        args = {
            'object_list': object_list, 'category_list': category_list, 'order': order
        }
        return render(request, self.template_name, args)


class CategoryView(ListView):
    template_name = "home.html"

    def get(self, request, *args, **kwargs):
        category_list = []
        for name, value in CATEGORY_CHOICES:
            for item in Item.objects.all():
                if item.category == value and value not in category_list:
                    category_list.append(value)

        for name, value in CATEGORY_CHOICES:
            if self.kwargs.get('slug') == value:
                object_list = Item.objects.filter(category=value).order_by('title')

                device = self.request.COOKIES['device']
                customer_qs = Customer.objects.filter(device=device)

                if customer_qs.exists():
                    customer = Customer.objects.filter(device=device).first()
                else:
                    customer = Customer.objects.create(device=device)

                order_qs = Order.objects.filter(customer=customer, ordered=False)

                if order_qs.exists():
                    order = Order.objects.get(customer=customer, ordered=False)
                else:
                    order = None

                args = {
                    'object_list': object_list, 'category_list': category_list, 'order': order
                }
                return render(request, self.template_name, args)


class OrderSummaryView(View):
    def get(self, *args, **kwargs):
        try:
            device = self.request.COOKIES['device']
            customer_qs = Customer.objects.filter(device=device)

            if customer_qs.exists():
                customer = Customer.objects.filter(device=device).first()
            else:
                customer = Customer.objects.create(device=device)

            order_qs = Order.objects.filter(customer=customer, ordered=False)

            if order_qs.exists():
                order = Order.objects.get(customer=customer, ordered=False)
            else:
                order = None

            context = {
                'order': order
            }
            return render(self.request, 'order_summary.html', context)

        except ObjectDoesNotExist:
            messages.warning(self.request, "No tiene un pedido activo.")
            return redirect("/")


class ItemDetailView(DetailView):
    template_name = "product.html"

    def get(self, request, slug):
        form = OrderItemForm()
        uniqueobject = get_object_or_404(Item, slug=slug)

        device = self.request.COOKIES['device']
        customer_qs = Customer.objects.filter(device=device)

        if customer_qs.exists():
            customer = Customer.objects.filter(device=device).first()
        else:
            customer = Customer.objects.create(device=device)

        order_qs = Order.objects.filter(customer=customer, ordered=False)

        if order_qs.exists():
            order = Order.objects.get(customer=customer, ordered=False)
        else:
            order = None

        args = {
            'form': form, 'uniqueobject': uniqueobject, 'order': order
        }
        return render(request, self.template_name, args)

    def post(self, request, slug):
        # get the user inputs from the form
        form = OrderItemForm(self.request.POST)
        item = get_object_or_404(Item, slug=slug)
        if form.is_valid():
            chosenSize = form.cleaned_data.get('chosenSize')
            chosenColor = form.cleaned_data.get('chosenColor')
            quantity = form.cleaned_data.get('quantity')

        # create the new OrderItem
        device = self.request.COOKIES['device']
        customer_qs = Customer.objects.filter(device=device)

        if customer_qs.exists():
            customer = Customer.objects.filter(device=device).first()
        else:
            customer = Customer.objects.create(device=device)

        newOrderItem = OrderItem()
        # newOrderItem.user = self.request.user
        newOrderItem.customer = customer
        newOrderItem.ordered = False
        newOrderItem.item = item
        newOrderItem.chosenSize = chosenSize
        newOrderItem.chosenColor = chosenColor
        newOrderItem.quantity = quantity
        newOrderItem.save()

        order_qs = Order.objects.filter(customer=customer, ordered=False)

        if order_qs.exists():
            order = Order.objects.get(customer=customer, ordered=False)
        else:
            order = None

        args = {'form': form, 'uniqueobject': item, 'order': order}
        add_to_cart(request, slug=slug, newOrderItem=newOrderItem)
        return render(request, self.template_name, args)


def add_to_cart(request, slug, newOrderItem):
    item = get_object_or_404(Item, slug=slug)
    order_item = newOrderItem

    device = request.COOKIES['device']
    customer_qs = Customer.objects.filter(device=device)

    if customer_qs.exists():
        customer = Customer.objects.filter(device=device).first()
    else:
        customer = Customer.objects.create(device=device)

    order_qs = Order.objects.filter(customer=customer, ordered=False)

    if order_qs.exists():
        order = order_qs[0]
        # check if the order item with same size and color is already in the order
        # if yes, get this existing object, update its quantity and save it
        if order.items.filter(item__slug=item.slug,
                              chosenSize=order_item.chosenSize,
                              chosenColor=order_item.chosenColor).exists():
            existingOrderItem = order.items.filter(item__slug=item.slug,
                                                   chosenSize=order_item.chosenSize,
                                                   chosenColor=order_item.chosenColor).get()
            existingOrderItem.quantity += order_item.quantity
            existingOrderItem.save()
            messages.info(request, "La cantidad de este artículo fue actualizada.")
            return redirect("core:order-summary")
        else:
            order.items.add(order_item)
            messages.info(request, "Este artículo ha sido añadido a su carrito.")
            return redirect("core:order-summary")

    else:
        ordered_date = timezone.now()
        order = Order.objects.create(
            customer=customer, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "Este artículo ha sido añadido a su carrito.")
        return redirect("core:order-summary")


def remove_from_cart(request, slug, chosen_size, chosen_color):
    device = request.COOKIES['device']
    customer_qs = Customer.objects.filter(device=device)

    if customer_qs.exists():
        customer = Customer.objects.filter(device=device).first()
    else:
        customer = Customer.objects.create(device=device)

    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(
        customer=customer,
        ordered=False,
    )

    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug,
                              chosenSize=chosen_size,
                              chosenColor=chosen_color).exists():
            order_item = OrderItem.objects.filter(
                item=item,
                customer=customer,
                chosenSize=chosen_size,
                chosenColor=chosen_color
            )[0]
            order.items.remove(order_item)
            order_item.delete()
            messages.info(request, "Este artículo ha sido eliminado de su carrito.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "Este artículo no estaba en su carrito.")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "No tiene un pedido activo.")
        return redirect("core:product", slug=slug)
