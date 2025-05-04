from django import forms
from django.contrib.auth import password_validation

from app_shop.models import Category


class ProductFilterForm(forms.Form):
    """ Форма сортировки и фильтрации товаров"""
    query = forms.CharField(max_length=100, required=False, label='Поиск', strip=True)

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        label='Категория'
    )
    min_price = forms.DecimalField(required=False, label='Цена от', min_value=0)
    max_price = forms.DecimalField(required=False, label='до', min_value=0)
    DATE_FILTER_CHOICES = (
        ('', 'Все'),
        ('7', 'Последние 7 дней'),
        ('30', 'Последние 30 дней'),
    )
    date_filter = forms.ChoiceField(choices=DATE_FILTER_CHOICES, required=False, label='Дата добавления')
    SORT_CHOICES = (
        ('date_desc', 'Новизне'),
        ('price_asc', 'Цене ↑'),
        ('price_desc', 'Цене ↓'),
        ('popular', 'Популярности'),
    )
    sort_by = forms.ChoiceField(choices=SORT_CHOICES, required=False, label='Сортировать по')

