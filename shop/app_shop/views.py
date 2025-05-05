from datetime import timedelta

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.paginator import Paginator
from django.db.models import Prefetch, OuterRef, Subquery, Value, CharField, Sum, F, Count, Q, Min, Max, Avg
from django.db.models.functions import Concat
from django.http import HttpRequest, HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils import timezone
from django.views import View
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView

from .forms import ProductFilterForm, ProductForm, CategoryForm
from .models import Product, ProductImage, CartItem, Category
from .services.session_cart import SessionCart, get_cart_info, get_cart_items


class ProductListView(ListView):
    """Списковое отображение модели Product"""
    model = Product
    queryset = Product.objects.filter(draft=False, deleted_at__isnull=True)
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
    ).filter(draft=False, deleted_at__isnull=True)

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
    queryset = Product.objects.filter(draft=False, deleted_at__isnull=True)


def product_detail(request: HttpRequest, *args, **kwargs) -> HttpResponse:
    product_id = kwargs.get("pk")
    product = get_object_or_404(Product, pk=product_id)
    context = {
        "product": product,
    }
    return render(request=request,
                  template_name="app_shop/product_detail.html",
                  context=context)


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Создание Товара :models:app_shop.Product"""
    model = Product
    permission_required = "app_shop.add_product"
    form_class = ProductForm
    template_name = "app_shop/product_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        self.object = form.save()
        images = self.request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=self.object, file=image, author=self.request.user)
        return redirect(self.get_success_url())


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Редактирование Товара :models:app_shop.Product"""
    model = Product
    permission_required = "app_shop.change_product"
    form_class = ProductForm
    template_name = "app_shop/product_form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        self.object = form.save()
        images = self.request.FILES.getlist('images')
        for image in images:
            ProductImage.objects.create(product=self.object, file=image, author=self.request.user)
        return redirect(self.get_success_url())


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Удаление Товара :models:app_shop.Product"""
    model = Product
    permission_required = "app_shop.delete_product"
    success_url = reverse_lazy('shop:products')

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        print(self.object)
        self.object.deleted_at = timezone.now()
        self.object.save()
        # return redirect(self.get_success_url())

        return HttpResponseRedirect(self.success_url)


class ProductImageDeleteView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Удаление Изображения Товара :models:app_shop.ProductImage"""
    permission_required = "app_shop.delete_productimage"

    def post(self, request, pk):
        image = get_object_or_404(ProductImage, pk=pk)
        if image.author == request.user or request.user.has_perm('app_shop.delete_productimage'):
            image.delete()
            return JsonResponse({"status": "deleted"})
        else:
            return JsonResponse({"status": "error", "message": "Недостаточно прав"}, status=403)


class ProductJsonSearchView(View):
    """Поиск товара по имени"""

    def get(self, request):
        query = request.GET.get('q', '').strip()
        print(query)

        if not query:
            return JsonResponse([], safe=False)

        products = Product.objects.filter(name__icontains=query).order_by("name").values('id', 'name', )[:10]
        return JsonResponse(list(products), safe=False)


class ProductSetCategoryView(LoginRequiredMixin, PermissionRequiredMixin, View):
    """Изменение категории товара/ привязывание товара к Категории"""
    permission_required = "app_shop.change_product"

    def post(self, request, product_pk, category_pk):
        product = get_object_or_404(Product, pk=product_pk)
        category = get_object_or_404(Category, pk= category_pk)
        product.category = category
        product.save(update_fields=["category", ])
        return JsonResponse({"status": "changed"})


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


class CategoryDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Детальный просмотр Категории :models:app_shop.Category"""
    model = Category
    permission_required = "app_shop.view_category"
    template_name = "app_shop/category_detail.html"
    queryset = Category.objects.annotate(product_counter=Count("product"))

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        subtree = category.get_descendants(include_self=True).annotate(product_counter=Count("product"))
        context["subtree"] = subtree
        return context


class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Списковый древовидный просмотр Категорий :models:app_shop.Category"""
    model = Category
    permission_required = "app_shop.view_category"
    template_name = "app_shop/category_list.html"
    queryset = (Category.objects.all()
                .annotate(
        product_counter=Count("product"),
        product_total_cost=Sum("product__price"),
        min_price=Min("product__price"),
        max_price=Max("product__price"),
        avg_price=Avg("product__price"),

    ))


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Создание Категории :models:app_shop.Category"""
    model = Product
    permission_required = "app:shop.add_catagory"
    form_class = CategoryForm
    template_name = "app_shop/category_form.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category_list = Category.objects.all()
        context["category_list"] = category_list
        return context


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Редактирование Категории :models:app_shop.Category"""
    model = Category
    permission_required = "app_shop.update_product"
    form_class = CategoryForm
    template_name = "app_shop/category_form.html"


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """Удаление Категории :models:app_shop.Category"""
    model = Category
    permission_required = "app_shop.delete_category"
    success_url = reverse_lazy('shop:products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        category = self.object
        subtree = category.get_descendants(include_self=True).annotate(product_counter=Count("product"))
        context["subtree"] = subtree
        return context
