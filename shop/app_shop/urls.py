from django.urls import path

from .views import product_detail, product_list, ProductListView, ProductDetailView, cart_view, add_to_cart, \
    remove_from_cart

app_name = "shop"

urlpatterns = [
    # path("products/<int:pk>", ProductDetailView.as_view(), name="products-detail"),
    path("products/<int:pk>", product_detail, name="products-detail"),
    path("", ProductListView.as_view(), name="products"),
    path('cart/', cart_view, name='cart_view'),
    path('add-to-cart/<int:product_id>/<int:quantity>', add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:product_id>/', remove_from_cart, name='remove_from_cart'),
]
