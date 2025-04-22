# app_shop/context_processors.py
from .services.session_cart import get_cart_info


def cart_context(request):
    """Добавление в context объекта корзина покупателя"""
    cart = get_cart_info(request)
    return {
        'context_cart': cart,
    }
