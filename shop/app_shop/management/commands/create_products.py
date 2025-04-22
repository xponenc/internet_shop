import os
import aiohttp
import asyncio
from random import randint
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from app_shop.models import Product, ProductImage
from asgiref.sync import sync_to_async

LOREM_IMAGE_URL = "https://picsum.photos/600/400"

User = get_user_model()


class Command(BaseCommand):
    help = "Создает в БД 20 тестовых товаров с изображениями"

    async def fetch_image(self, session, url):
        """Асинхронная загрузка изображения."""
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            return None

    async def create_product_with_images(self, session, author, product_number):
        """Создаёт продукт и загружает к нему изображения."""
        product = await sync_to_async(Product.objects.create)(
            name=f"Product {product_number}",
            description=f"Описание товара {product_number}" * 30,
            price=randint(100, 10000) / 100,
            author=author,
        )
        self.stdout.write(self.style.SUCCESS(f"Создан товар: {product.name}"))

        tasks = []
        for j in range(3):  # 3 изображения
            tasks.append(self.fetch_image(session, LOREM_IMAGE_URL))

        images = await asyncio.gather(*tasks)

        for j, image_data in enumerate(images):
            if image_data:
                image_name = f"{product.id}_{j+1}.jpg"
                product_image = ProductImage(
                    product=product,
                    author=author,
                )
                await sync_to_async(product_image.file.save)(image_name, ContentFile(image_data), save=True)
                self.stdout.write(self.style.SUCCESS(f"Добавлено изображение {image_name}"))

    async def populate_products(self, author):
        """Асинхронно создаёт товары и загружает к ним изображения."""
        async with aiohttp.ClientSession() as session:
            tasks = [self.create_product_with_images(session, author, i + 1) for i in range(20)]
            await asyncio.gather(*tasks)

        self.stdout.write(self.style.SUCCESS("Все товары и изображения успешно добавлены!"))

    def handle(self, *args, **kwargs):
        """Запуск команды."""
        author, created = User.objects.get_or_create(
            username="test_user",
            defaults={"email": "test_user@example.com"},
        )
        if created:
            author.set_password("testpassword")
            author.save()
            self.stdout.write(self.style.SUCCESS("Создан пользователь test_user"))

        asyncio.run(self.populate_products(author))
