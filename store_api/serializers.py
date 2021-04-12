from rest_framework import serializers

class CustomerSerializer(serializers.Serializer):

    limit = serializers.IntegerField(required=False,default=10)
    offset = serializers.IntegerField(required=False,default=0)
    

class CustomerProductsSerializer(serializers.Serializer):

    limit = serializers.IntegerField(required=False,default=10)
    offset = serializers.IntegerField(required=False,default=0)


class CustomerOrdersSerializer(serializers.Serializer):

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)
    limit = serializers.IntegerField(required=False,default=10)
    offset = serializers.IntegerField(required=False,default=0)


class OrdersProductsSerializer(serializers.Serializer):
    
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField()


class OrdersSerializer(serializers.Serializer):

    products = serializers.ListField(allow_empty=False, 
                                     max_length=5)
    delivery_address = serializers.CharField(max_length=150, allow_blank=True)