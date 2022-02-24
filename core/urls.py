from django.urls import path
from .views import (
    ItemDetailView,
    CheckoutView,
    HomeView, ProjectView, CategoryView,
    OrderSummaryView,
    add_to_cart,
    remove_from_cart
)

app_name = 'core'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('category/<slug>/', CategoryView.as_view(), name='category'),
    path('checkout/', CheckoutView.as_view(), name='checkout'),
    path('order-summary/', OrderSummaryView.as_view(), name='order-summary'),
    path('product/<slug>/', ItemDetailView.as_view(), name='product'),
    path('add-to-cart/<slug>/', add_to_cart, name='add-to-cart'),
    path('remove-from-cart/<slug:slug>/<str:chosen_size>/<str:chosen_color>/', remove_from_cart,
         name='remove-from-cart'),
    path('projects/', ProjectView.as_view(), name='projects'),
]
