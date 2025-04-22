import os

from django.db import models
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.urls import reverse

from app_user.models import SiteUser


class Product(models.Model):
    """Модель Товара"""
    name = models.CharField(verbose_name="название", max_length=200, unique=True)
    description = models.TextField(verbose_name="описание")
    price = models.DecimalField(verbose_name="цена", max_digits=10, decimal_places=2)
    draft = models.BooleanField(verbose_name="удален", default=False)
    author = models.ForeignKey(SiteUser, verbose_name="создал/изменил", on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name="дата создания", auto_now_add=True)
    updated_at = models.DateTimeField(verbose_name="дата редактирования", auto_now=True)
    deleted_at = models.DateTimeField(verbose_name="дата удаления", blank=True, null=True)

    objects = models.Manager()

    class Meta:
        verbose_name = "товар"
        verbose_name_plural = "товары"
        ordering = ["name", "-created_at", "-updated_at", ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:products-detail', args=[str(self.id)])


class ProductImage(models.Model):
    """Модель изображения Товара :model:'app_shop:Product'"""

    def image_path(self, filename):
        return os.path.join('products', 'images', str(self.product.id), filename)

    product = models.ForeignKey(Product, verbose_name="товар", on_delete=models.CASCADE)
    file = models.ImageField(verbose_name="изображения", upload_to=image_path)
    author = models.ForeignKey(SiteUser, verbose_name="создал/изменил", on_delete=models.PROTECT)
    created_at = models.DateTimeField(verbose_name="дата создания", auto_now_add=True)

    objects = models.Manager()

    class Meta:
        verbose_name = "изображение товара"
        verbose_name_plural = "изображения товаров"
        ordering = ["-created_at", ]

    def __str__(self):
        return f"ProductImage({self.file.name}) for Product(id={self.product.pk}, name={self.product.name})"


@receiver(pre_delete, sender=ProductImage)
def image_model_delete(sender, instance, **kwargs):
    """Физическое удаление файлов при удалении экземпляра модели"""
    if instance.image.name:
        instance.image.delete(False)


class Cart(models.Model):
    """Модель корзины Пользователя"""
    user = models.OneToOneField(SiteUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = models.Manager()


class CartItem(models.Model):
    """Модель позиция товара в Корзине :model:'app_shop.Cart'"""
    cart = models.ForeignKey(Cart, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    objects = models.Manager()

