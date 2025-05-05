from django import forms
from django.contrib.auth import password_validation

from app_shop.models import Category, Product, ProductImage


class CategoryForm(forms.ModelForm):
    """Форма создания/изменения Категории :models:app_shop.Category"""

    class Meta:
        model = Category
        exclude = ["deleted_at", ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['parent'].widget.attrs.update({
            'class': 'custom-field__input',
            'placeholder': '',
        })
        self.fields['name'].widget.attrs.update({
            'class': 'custom-field__input',
            'placeholder': ' ',
        })


class ProductForm(forms.ModelForm):
    """Форма создания/изменения Товара :models:app_shop.Product"""

    images = forms.FileField(widget=forms.FileInput(), required=False,
                             label="изображение")

    class Meta:
        model = Product
        exclude = ["author", "created_at", "updated_at", "deleted_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].widget.attrs.update({
            'class': 'custom-field__input',
            'placeholder': '',
        })
        self.fields['name'].widget.attrs.update({
            'class': 'custom-field__input',
            'placeholder': ' ',
        })
        self.fields['price'].widget.attrs.update({
            'class': 'custom-field__input',
            'placeholder': ' ',
        })

        self.fields['description'].widget.attrs.update({
            'class': 'custom-field__input custom-field__input_wide custom-field__input_textarea',
            'placeholder': ' ',
        })


class ProductImageCreateForm(forms.ModelForm):
    """Форма создания Изображения Товара"""

    class Meta:
        model = ProductImage
        fields = ["file", ]


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

