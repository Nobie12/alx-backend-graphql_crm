from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone

class Customer(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)  # optional
    created_at = models.DateTimeField(auto_now_add=True)



    def __str__(self):
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)  # required by default
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]  # positive decimal
    )
    stock = models.PositiveIntegerField(default=0, null=True, blank=True)

    def __str__(self):
        return self.name


class Order(models.Model):
    customer = models.ForeignKey(
        'Customer',
        on_delete=models.CASCADE,
        related_name='orders'
    )
    products = models.ManyToManyField(
        'Product',
        related_name='orders'
    )
    order_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)



    def __str__(self):
        return f"Order {self.id} for {self.customer.name}"
