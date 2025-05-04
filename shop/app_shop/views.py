from datetime import timedelta

from django.conf import settings
from django.core.paginator import Paginator
from django.db.models import Prefetch, OuterRef, Subquery, Value, CharField, Sum, F
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.generic import ListView, DetailView

from .forms import ProductFilterForm
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

    filter_ordering_form = ProductFilterForm(request.GET or None)
    first_image_subquery = ProductImage.objects.filter(
        product=OuterRef("id")).order_by("created_at").values("file")[:1]
    products = Product.objects.all().select_related("category").order_by("created_at").annotate(
        first_image_url=Concat(
            Value(settings.MEDIA_URL),  # Добавляем MEDIA_URL перед путем
            Subquery(first_image_subquery, output_field=CharField())
        )
    )

    if filter_ordering_form.is_valid():
        cd = filter_ordering_form.cleaned_data
        # Поиск по названию
        query = cd.get('query')
        if query:
            products = products.filter(name__icontains=query)

        if cd['category']:
            # Получаем все потомки выбранной категории (включая её саму)
            category = cd['category']
            descendants = category.get_descendants(include_self=True)
            products = products.filter(category__in=descendants)

        if cd['min_price'] is not None:
            products = products.filter(price__gte=cd['min_price'])

        if cd['max_price'] is not None and cd['max_price'] < float('inf'):
            products = products.filter(price__lte=cd['max_price'])

        if cd['date_filter']:
            days = int(cd['date_filter'])
            cutoff_date = timezone.now() - timedelta(days=days)
            products = products.filter(created_at__gte=cutoff_date)

        # Сортировка
        sort_by = cd.get('sort_by', 'date_desc')
        if sort_by == 'price_asc':
            products = products.order_by('price')
        elif sort_by == 'price_desc':
            products = products.order_by('-price')
        elif sort_by == 'popular':
            products = products.annotate(
                total_sold=Sum('orderitem__quantity')
            )
            products = products.order_by('-total_sold')

    paginator = Paginator(products, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    is_paginated = paginator.num_pages > 1
    # --- Формируем paginator_query ---
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    paginator_query = query_params.urlencode() + "&"
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        data = {
            'html': render_to_string(
                'app_shop/include/_body-product-list.html',
                {
                    'paginator': paginator,
                    'page_obj': page_obj,
                    'is_paginated': is_paginated,
                    'paginator_query': paginator_query,
                })
        }
        return JsonResponse(data)

    return render(request, 'app_shop/product_list.html', {
        'filter_ordering_form': filter_ordering_form,
        'paginator': paginator,
        'page_obj': page_obj,
        'is_paginated': is_paginated,
        'paginator_query': paginator_query,

    })


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
