import graphene
from graphene_django import DjangoObjectType
from .models import Customer, Product, Order
from crm.models import Product
from .filters import CustomerFilter, ProductFilter, OrderFilter
from graphene_django.filter import DjangoFilterConnectionField
from graphql import GraphQLError
from decimal import Decimal
from django.utils import timezone
from django.db import transaction

import re

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ('id', 'name', 'email', 'phone')
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ('id', 'name', 'price', 'stock')
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ('id', 'customer', 'products', 'order_date', 'total_amount')
        interfaces = (graphene.relay.Node,)


class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String(required=False)
    
    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise GraphQLError("Email already exists")
        
        if phone:
            phone = phone.strip()
            if not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
                raise GraphQLError("Invalid phone format")

        
        customer = Customer(name=name, email=email, phone=phone)
        customer.save()

        return CreateCustomer(customer=customer, message="Customer created successfully")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers = graphene.List(
            graphene.NonNull(lambda: CustomerInput), required=True
        )
    
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers):
        errors = []
        created = []

        with transaction.atomic():
            for customer in customers:
                try:
                    if Customer.objects.filter(email=customer.email).exists():
                        errors.append(f"Email {customer.email} already exists")
                        continue
                    
                    if customer.phone:
                        phone = customer.phone.strip()
                        if not re.match(r'^(\+\d{10,15}|\d{3}-\d{3}-\d{4})$', phone):
                            errors.append(f"Invalid phone format for {customer.name}")
                            continue
                    
                    customer = Customer(
                        name=customer.name,
                        email=customer.email,
                        phone=customer.phone
                    )
                    
                    customer.save()
                    created.append(customer)
                except Exception as e:
                    errors.append(str(e))

        return BulkCreateCustomers(customers=created, errors=errors)


class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Float(required=True)
        stock = graphene.Int(required=False)
    
    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock):
        if price <= 0:
            raise GraphQLError("Price must be positive")
        if stock < 0:
            raise GraphQLError("Stock cannot be negative")
        
        product = Product(name=name, price=Decimal(price), stock=stock)
        product.save()

        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.NonNull(graphene.ID), required=True)
        order_date = graphene.DateTime(required=False)
    
    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids, order_date=None):
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Invalid customer ID")
        
        if not product_ids:
            raise GraphQLError("At least one product is required")
        
        products = []
        total_amount = Decimal(0)

        for pid in product_ids:
            try:
                product = Product.objects.get(id=pid)
                products.append(product)
                total_amount += product.price
            except Product.DoesNotExist:
                raise GraphQLError(f"Invalid product ID: {pid}")

        order = Order.objects.create(
            customer=customer,
            total_amount=total_amount,
            order_date=order_date or timezone.now()
        )
        order.products.set(products)
        return CreateOrder(order=order)

class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        stock_threshold = graphene.Int(default_value=10)

    products = graphene.List(ProductType)
    message = graphene.String()

    def mutate(self, info, stock_threshold=10):
        restock_quantity = 10

        # products with stock < 10
        products = Product.objects.filter(stock__lt=stock_threshold)

        # increment each product by 10 simulating restocking
        for product in products:
            product.stock += restock_quantity
            product.save()
        return UpdateLowStockProducts(products=products, messages="Restock completed successfully")

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()


class Query(graphene.ObjectType):
    # Add order_by argument for sorting
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        order_by=graphene.List(of_type=graphene.String)
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
        order_by=graphene.List(of_type=graphene.String)
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        order_by=graphene.List(of_type=graphene.String)
    )

    # Override resolver to support order_by sorting
    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return qs

schema = graphene.Schema(query=Query, mutation=Mutation)
