from django.db import models
from django.core.validators import MinValueValidator
from django.db.models import Prefetch, Count
from phonenumber_field.modelfields import PhoneNumberField


class Restaurant(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    address = models.CharField(
        'адрес',
        max_length=100,
        blank=True,
    )
    contact_phone = models.CharField(
        'контактный телефон',
        max_length=50,
        blank=True,
    )

    class Meta:
        verbose_name = 'ресторан'
        verbose_name_plural = 'рестораны'

    def __str__(self):
        return self.name


class ProductQuerySet(models.QuerySet):
    def available(self):
        products = (
            RestaurantMenuItem.objects
                .filter(availability=True)
                .values_list('product')
        )
        return self.filter(pk__in=products)


class ProductCategory(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'категории'

    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(
        'название',
        max_length=50
    )
    category = models.ForeignKey(
        ProductCategory,
        verbose_name='категория',
        related_name='products',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    price = models.DecimalField(
        'цена',
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    image = models.ImageField(
        'картинка'
    )
    special_status = models.BooleanField(
        'спец.предложение',
        default=False,
        db_index=True,
    )
    description = models.TextField(
        'описание',
        max_length=200,
        blank=True,
    )

    objects = ProductQuerySet.as_manager()

    class Meta:
        verbose_name = 'товар'
        verbose_name_plural = 'товары'

    def __str__(self):
        return self.name


class RestaurantMenuItem(models.Model):
    restaurant = models.ForeignKey(
        Restaurant,
        related_name='menu_items',
        verbose_name="ресторан",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name='продукт',
    )
    availability = models.BooleanField(
        'в продаже',
        default=True,
        db_index=True
    )

    class Meta:
        verbose_name = 'Пункт меню ресторана'
        verbose_name_plural = 'Пункты меню ресторана'
        unique_together = [
            ['restaurant', 'product']
        ]

    def __str__(self):
        return f"{self.restaurant.name} - {self.product.name}"


# class OrderQuerySet(models.QuerySet):
#     def prefetch_items(self):
#         orders = Order.objects.exclude(status=Order.READY).order_by('-status').select_related(
#             'restaurant').prefetch_related('items__product')
#
#         menu_items = RestaurantMenuItem.objects.filter(availability=True).values('restaurant', 'product')
#         restaurants = Restaurant.objects.in_bulk([item['restaurant'] for item in menu_items])
#
#         orders = orders.annotate(product_count=Count('items__product'))
#
#         for order in orders:
#             if order.restaurant is None:
#                 order_restaurants = []
#                 order_products = order.items.all()
#                 for restaurant in restaurants:
#                     restaurants_possible = True
#                     for order_product in order_products:
#                         restaurants_for_product = menu_items.filter(product=order_product.product,
#                                                                     restaurant=restaurants[restaurant])
#                         if not restaurants_for_product:
#                             restaurants_possible = False
#                     if restaurants_possible:
#                         order_restaurants.append(restaurants[restaurant])
#
#                 if order_restaurants:
#                     order.restaurant_possible = order_restaurants
#         return orders

class OrderQuerySet(models.QuerySet):
    def prefetch_items(self):
        menu_items = RestaurantMenuItem.objects.filter(availability=True).values('restaurant', 'product')
        restaurants = Restaurant.objects.in_bulk(set(item['restaurant'] for item in menu_items))

        orders = self.exclude(status=Order.READY).order_by('-status')

        orders = orders.select_related('restaurant').prefetch_related(
            Prefetch('items__product', queryset=Product.objects.only('id', 'name'))).annotate(
            product_count=Count('items__product'))

        # Получаем все идентификаторы заказов
        order_ids = [order.pk for order in orders]
        order_items = OrderItem.objects.filter(order_id__in=order_ids).values('order_id', 'product_id')

        # Создаем словарь для хранения связей между заказами и продуктами
        order_products = {}
        for item in order_items:
            order_id = item['order_id']
            product_id = item['product_id']
            if order_id not in order_products:
                order_products[order_id] = []
            order_products[order_id].append(product_id)

        # Создаем словарь для хранения связей между заказами и ресторанами
        order_restaurants = {}
        for order_id, restaurant in restaurants.items():
            restaurants_possible = True

            if order_id in order_products:
                order_product_ids = order_products[order_id]
                for product_id in order_product_ids:
                    if not menu_items.filter(product_id=product_id, restaurant=order_id).exists():
                        restaurants_possible = False
                        break

            if restaurants_possible:
                if order_id not in order_restaurants:
                    order_restaurants[order_id] = []
                order_restaurants[order_id].append(restaurant)

        # Присваиваем список ресторанов, доступных для каждого заказа
        for order in orders:
            if order.pk in order_restaurants:
                order.restaurant_possible = order_restaurants[order.pk]
            else:
                order.restaurant_possible = []

        return orders


class Order(models.Model):
    CASH = 'CASH'
    ELECTRONICALLY = 'ELECTRON'
    PAY_TYPE = [
        (CASH, 'Наличными'),
        (ELECTRONICALLY, 'Электронно'),
    ]
    pay = models.CharField(
        'Способ оплаты',
        choices=PAY_TYPE,
        max_length=20,
        db_index=True,

    )

    NEW = 'new'
    COOKING = 'cooking'
    DELIVERY = 'delivery'
    READY = 'ready'
    ORDER_STATUS = [
        (NEW, 'Необработанный'),
        (COOKING, 'Готовится'),
        (DELIVERY, 'Доставка'),
        (READY, 'Доставлен'),
    ]
    status = models.CharField(
        'Статус заказа',
        choices=ORDER_STATUS,
        default=NEW,
        max_length=20,
        db_index=True
    )
    firstname = models.CharField(
        'Имя',
        max_length=90
    )
    lastname = models.CharField(
        'Фамилия',
        max_length=100,
        db_index=True
    )

    phone_number = PhoneNumberField(
        verbose_name='Телефон',
        db_index=True
    )

    address = models.CharField(
        'Адрес доставки',
        max_length=100,
    )
    total_price = models.DecimalField(
        'Сумма заказа',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(
            limit_value=0
        )])
    comment = models.TextField(
        blank=True, verbose_name='Комментарий к заказу'
    )
    registration_date = models.DateTimeField(
        blank=True, null=True, verbose_name='Дата регистрации', db_index=True, auto_now=True
    )
    call_date = models.DateTimeField(
        blank=True, null=True, verbose_name='Дата звонка', db_index=True
    )
    delivery_date = models.DateTimeField(
        blank=True, null=True, verbose_name='Дата доставки', db_index=True
    )

    restaurant = models.ForeignKey(
        Restaurant,
        verbose_name='Ресторан',
        blank=True,
        null=True,
        on_delete=models.CASCADE
    )
    objects = OrderQuerySet.as_manager()

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'

    def __str__(self):
        return f'{self.firstname} {self.phone_number}'

    def get_total_cost(self):
        # общая сумма заказа
        return sum(item.get_cost() for item in self.items.all())


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        related_name='items',
        verbose_name="Заказы",
        on_delete=models.CASCADE,
    )
    product = models.ForeignKey(
        Product,
        related_name='products',
        verbose_name="Продукты",
        on_delete=models.CASCADE,
    )
    quantity = models.IntegerField('Количество')
    price = models.DecimalField(
        'Сумма',
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(
            limit_value=0
        )],
    )

    class Meta:
        verbose_name = 'Заказ'
        verbose_name_plural = 'Заказы'
        unique_together = ('order', 'product')

    def __str__(self):
        return f"{self.order.phone_number} - {self.product.name}"

    def get_cost(self):
        return self.product.price * self.quantity
