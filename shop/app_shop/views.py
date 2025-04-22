from django.conf import settings
from django.db.models import Prefetch, OuterRef, Subquery, Value, CharField, Sum, F
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView

from .models import Product, ProductImage, CartItem
from .services.session_cart import SessionCart, get_cart_info, get_cart_items


class ProductListView(ListView):
    """Списковое отображение модели Product"""
    model = Product
    queryset = Product.objects.filter(draft=False)
    paginate_by = 9

    def get_queryset(self):
        queryset = super().get_queryset()
        first_image_subquery = ProductImage.objects.filter(
            product=OuterRef("id")).order_by("created_at").values("file")[:1]

        return queryset.annotate(
            first_image_url=Concat(
                Value(settings.MEDIA_URL),  # Добавляем MEDIA_URL перед путем
                Subquery(first_image_subquery, output_field=CharField())
            )
        )


def product_list(request: HttpRequest) -> HttpResponse:
    """Списковое отображение модели Product"""
    products = Product.objects.prefetch_related("productimage_set").filter(draft=False)
    context = {
        "product_list": products,
    }
    return render(request=request,
                  template_name="app_shop/product_list.html",
                  context=context)


class ProductDetailView(DetailView):
    """Детальное отображение модели Product"""
    model = Product


def product_detail(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    product_id = kwargs.get("pk")
    product = get_object_or_404(Product, pk=product_id)
    context = {
        "product": product,
    }
    return render(request=request,
                  template_name="app_shop/product_detail.html",
                  context=context)


def add_to_cart(request, product_id, quantity):
    """Добавляет товар в корзину."""
    print(">> add_to_cart")
    if request.user.is_authenticated:
        cart = request.user.cart
        cart_item = cart.items.filter(product_id=product_id).first()

        if cart_item:
            cart_item.quantity += quantity
            cart_item.save()
        else:
            product = get_object_or_404(Product, id=product_id)
            cart_item = CartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity
            )

    else:
        session_cart = SessionCart(request)
        session_cart.add(product_id=product_id, quantity=quantity)

    cart_info = get_cart_info(request)

    return JsonResponse({
        'success': True,
        'total_price': cart_info["total_price"],
        'total_quantity': cart_info["total_quantity"],
    })


def cart_view(request):
    """Отображает содержимое корзины."""
    cart_items = get_cart_items(request)

    context = {
        'cart_items': cart_items,
    }
    return render(request, 'app_shop/cart.html', context)


def remove_from_cart(request, product_id):
    """Удаляет товар из корзины."""
    if request.user.is_authenticated:
        # cart = request.user.cart
        # cart_item = cart.items.filter(product_id=product_id).first()
        CartItem.objects.filter(cart__user=request.user, product_id=product_id).delete()
    else:
        session_cart = SessionCart(request)
        session_cart.remove(product_id)

    cart_info = get_cart_info(request)

    return JsonResponse({
        'success': True,
        'total_price': cart_info["total_price"],
        'total_quantity': cart_info["total_quantity"],
    })