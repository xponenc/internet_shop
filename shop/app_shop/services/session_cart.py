from django.db.models import Sum, F
from django.db.models.functions import Round
from django.shortcuts import get_object_or_404
from ..models import Product, Cart, CartItem


class SessionCart:
    """Класс для управления корзиной в сессии для неавторизованного пользователя"""

    def __init__(self, request):
        self.request = request
        self.session = request.session
        self.cart = self.session.get('cart', {})

    def add(self, product_id, quantity=1):
        """Добавляет товар в корзину или увеличивает количество."""
        product = get_object_or_404(Product, id=product_id)
        product_id = str(product_id)  # Ключи в сессии — строки
        if product_id in self.cart:
            self.cart[product_id]['quantity'] += quantity
        else:
            self.cart[product_id] = {'quantity': quantity}
        self.save()

    def save(self):
        """Сохраняет корзину в сессию."""
        self.session['cart'] = self.cart
        self.session.modified = True

    def remove(self, product_id):
        """Удаляет товар из корзины."""
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def get_items(self):
        """Возвращает элементы корзины для отображения."""
        product_ids = self.cart.keys()
        cart_items = []
        cart_products = Product.objects.filter(id__in=product_ids).prefetch_related('productimage_set')
        for product in cart_products:
            cart_items.append({
                "quantity": self.cart[str(product.id)]["quantity"],
                "product": product,
                "cost": product.price * self.cart[str(product.id)]["quantity"],
            })

        return cart_items

    def clear(self):
        """Очищает корзину."""
        self.cart = {}
        self.save()

    def get_total_info(self):
        """Возвращает общую стоимость корзины и количество товаров"""
        product_ids = self.cart.keys()
        products = Product.objects.filter(id__in=product_ids)

        total_price = 0
        total_quantity = 0

        for product in products:
            quantity = self.cart[str(product.id)]['quantity']
            total_price += product.price * quantity
            total_quantity += quantity

        return {
            'total_price': total_price,
            'total_quantity': total_quantity
        }


def merge_session_cart_to_user_cart(request):
    """Переносит товары из сессионной корзины в корзину пользователя :model:'app_shop.Cart'"""
    if not request.user.is_authenticated:
        return

    session_cart = SessionCart(request)
    if not session_cart.cart:
        return

    user_cart, created = Cart.objects.get_or_create(user=request.user)

    for product_id, item_data in session_cart.cart.items():
        product = get_object_or_404(Product, id=product_id)
        cart_item, created = CartItem.objects.get_or_create(
            cart=user_cart,
            product=product,
            defaults={'quantity': item_data['quantity']}
        )
        if not created:
            cart_item.quantity += item_data['quantity']
            cart_item.save()

    # Очищаем сессионную корзину
    session_cart.clear()


def get_cart_info(request):
    """Возвращает словарь с состоянием корзины"""
    if request.user.is_authenticated:
        cart = Cart.objects.filter(user=request.user).annotate(
            total_price=Round(Sum(F('items__quantity') * F('items__product__price')), 2),
            total_quantity=Sum('items__quantity')
        ).first()

        if not cart:
            cart = Cart.objects.create(user=request.user)
            cart.total_price = 0
            cart.total_quantity = 0
        total_info = {
            "total_price": cart.total_price,
            "total_quantity": cart.total_quantity,
        }

    else:
        session_cart = SessionCart(request)
        total_info = session_cart.get_total_info()

    return total_info


def get_cart_items(request):
    """Возвращает элементы корзины для отображения."""
    if request.user.is_authenticated:
        cart = request.user.cart
        cart_items = (
            cart.items.select_related('product').prefetch_related('product__productimage_set')
            .annotate(
                cost=F('quantity') * F('product__price')
            ))
    else:
        session_cart = SessionCart(request)
        cart_items = session_cart.get_items()
    return cart_items
