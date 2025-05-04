import os
import aiohttp
import asyncio
from random import randint, choice, sample
from datetime import date
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.db import IntegrityError

from app_user.models import SiteUser, Profile
from app_shop.models import Product, ProductImage, Category, Order, OrderItem
from faker import Faker


LOREM_IMAGE_URL = "https://picsum.photos/600/400"

fake = Faker("ru_RU")


class Command(BaseCommand):
    help = "Создаёт тестовые данные: категории, товары, изображения, пользователи, профили и заказы"

    async def fetch_image(self, session, url):
        """Асинхронная загрузка изображения."""
        async with session.get(url) as response:
            if response.status == 200:
                return await response.read()
            return None

    def create_images_for_product(self, product, count=3):
        loop = asyncio.new_event_loop()
        images = loop.run_until_complete(self.async_download_images(count))
        for idx, image_data in enumerate(images):
            if image_data:
                ProductImage.objects.create(
                    product=product,
                    author=product.author,
                    file=ContentFile(image_data, name=f"{product.id}_{idx+1}.jpg")
                )
                self.stdout.write(self.style.SUCCESS(f"Изображение {idx+1} для {product.name} добавлено"))

    async def async_download_images(self, count):
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch_image(session, LOREM_IMAGE_URL) for _ in range(count)]
            return await asyncio.gather(*tasks)

    def handle(self, *args, **kwargs):
        # 1. Создать автора-администратора
        author, created = SiteUser.objects.get_or_create(
            email="test_author@example.com",
            defaults={
                "password": make_password("testpassword"),
                "phone_number": "+79990000000",
                "address": "ул. Пушкина, д. Колотушкина",
                "is_active": True,
            }
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Создан пользователь test_author"))

        # 2. Создать категории
        main_categories = []
        for i in range(5):
            cat = Category.objects.create(name=f"Категория {i + 1}")
            main_categories.append(cat)

        for main_cat in main_categories:
            for i in range(2):  # по 2 подкатегории
                subcat = Category.objects.create(
                    name=f"{main_cat.name} - Подкатегория {i + 1}",
                    parent=main_cat
                )
                for p in range(10):  # по 10 товаров в подкатегорию
                    product = Product.objects.create(
                        name=f"{subcat.name} Товар {p + 1}",
                        description=f"Описание товара {p + 1} категории {subcat.name}." * 10,
                        price=randint(100, 10000) / 100,
                        category=subcat,
                        author=author
                    )
                    self.stdout.write(self.style.SUCCESS(f"Создан товар: {product.name}"))
                    self.create_images_for_product(product)

        self.stdout.write(self.style.SUCCESS("Все категории и товары созданы!"))

        # 3. Создать пользователей и профили
        users = []
        for i in range(10):
            email = fake.email()
            phone = "+7" + str(randint(9000000000, 9999999999))
            address = fake.address().replace('\n', ', ')
            print(email)
            user = SiteUser.objects.create(
                email=email,
                password=make_password("testpassword"),
                phone_number=phone,
                address=address,
            )


            birthdate = fake.date_between(start_date="-50y", end_date="-18y")
            Profile.objects.create(
                user=user,
                birthdate=birthdate,
                bio=fake.text(max_nb_chars=200),
            )

            users.append(user)
            self.stdout.write(self.style.SUCCESS(f"Создан пользователь: {user.email}"))

        self.stdout.write(self.style.SUCCESS("Все пользователи и профили созданы!"))

        # 4. Создать заказы
        all_products = list(Product.objects.all())
        for user in users:
            num_orders = randint(3, 6)
            for _ in range(num_orders):
                order = Order.objects.create(user=user)
                selected_products = sample(all_products, k=randint(1, min(10, len(all_products))))
                items = [
                    OrderItem(order=order, product=product, quantity=randint(1, 5))
                    for product in selected_products
                ]
                OrderItem.objects.bulk_create(items)
                self.stdout.write(self.style.SUCCESS(f"Создан заказ №{order.id} для {user.email}"))

        self.stdout.write(self.style.SUCCESS("✅ Все тестовые данные успешно созданы!"))