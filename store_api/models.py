# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=191)
    email = models.CharField(unique=True, max_length=191)

    class Meta:
        managed = False
        db_table = 'customer'


class CustomerProduct(models.Model):
    customer = models.OneToOneField(Customer, models.DO_NOTHING, primary_key=True)
    product = models.ForeignKey('Product', models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'customer_product'
        unique_together = (('customer', 'product'),)


class Order(models.Model):
    order_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customer, models.DO_NOTHING)
    creation_date = models.DateField()
    delivery_address = models.CharField(max_length=191)
    total = models.FloatField()

    class Meta:
        managed = False
        db_table = 'order'


class OrderDetail(models.Model):
    order_detail_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, models.DO_NOTHING)
    product = models.ForeignKey('Product', models.DO_NOTHING)
    product_description = models.CharField(max_length=191)
    price = models.FloatField()
    quantity = models.PositiveIntegerField()

    class Meta:
        managed = False
        db_table = 'order_detail'


class Product(models.Model):
    product_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=191)
    product_description = models.CharField(max_length=191)
    price = models.FloatField()

    class Meta:
        managed = False
        db_table = 'product'
