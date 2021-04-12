from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, exceptions

from store_api import serializers

from store_api.models import Customer, CustomerProduct, Order, Product, OrderDetail
from django.db.models import Q

import datetime


class Paginator:
  @staticmethod
  def pagination(count, limit, offset, path, query_params={}):

        comp = []
        for key in query_params:
            if key!='limit' and key!='offset':
                comp.append(f"{key}={query_params[key]}")
        
        comp = '&'.join(comp)

        if limit+offset>=count:
            next_page = None
        else:
            next_limit = min([count-limit-offset,limit])
            next_offset = limit+offset
            next_page = path+f'?limit={next_limit}&offset={next_offset}'
            if comp!='':
                next_page += '&'+comp
        
        if not offset:
            previous_page = None
        else:
            previous_limit = min([offset,limit])
            previous_offset = max(0,offset-limit)
            previous_page = path+f'?limit={previous_limit}&offset={previous_offset}'
            if comp!='':
                previous_page += '&'+comp
        
        return next_page, previous_page


class CustomersView(APIView):

    serializerCustomer_class = serializers.CustomerSerializer

    def get(self, request, format=None):

        serializer = self.serializerCustomer_class(data=request.query_params)

        if serializer.is_valid():
            limit = serializer.validated_data.get('limit')
            offset = serializer.validated_data.get('offset')

            all_entries = Customer.objects.all()[offset:limit+offset]
            count = Customer.objects.count()

            next_page, previous_page = Paginator.pagination(count, limit, offset, request.path)

            customers = [{'customer_id': entry.customer_id, 'name': entry.name, 'email': entry.email} for entry in all_entries]

            return Response({'count': count, 'next': next_page, 'previous': previous_page, 'results': customers})

        else:
            return Response(
                serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )




class CustomerProductsView(APIView):

    serializerCustomerProducts_class = serializers.CustomerSerializer

    def get(self, request, customer_id, format=None):

            serializer = self.serializerCustomerProducts_class(data=request.query_params)

            if serializer.is_valid():
                limit = serializer.validated_data.get('limit')
                offset = serializer.validated_data.get('offset')

                all_entries = CustomerProduct.objects.select_related('product').filter(customer_id=customer_id).all()[offset:limit+offset]
                count = CustomerProduct.objects.select_related('product').filter(customer_id=customer_id).count()

                next_page, previous_page = Paginator.pagination(count, limit, offset, request.path)

                products = [{'product_id': entry.product_id, 'name': entry.product.name, 'product_description': entry.product.product_description, 'price': entry.product.price} for entry in all_entries]

                return Response({'count': count, 'next': next_page, 'previous': previous_page, 'results': products})

            else:
                return Response(
                    serializer.errors,
                    status = status.HTTP_400_BAD_REQUEST
                )

    

class CustomerOrdersAllView(APIView):

    serializer_class = serializers.OrdersSerializer
    serializerProducts_class = serializers.OrdersProductsSerializer
    serializerCustomerOrders_class = serializers.CustomerOrdersSerializer

    def get(self, request, customer_id, format=None):
            
        self.customer_id = customer_id

        serializer = self.serializerCustomerOrders_class(data=request.query_params)

        if serializer.is_valid():
            start_date = serializer.validated_data.get('start_date')
            end_date = serializer.validated_data.get('end_date')

            limit = serializer.validated_data.get('limit')
            offset = serializer.validated_data.get('offset')

            if (start_date is None and end_date is None) :
                all_entries = Order.objects.filter(customer=self.customer_id).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id).count()
            elif start_date is None:
                all_entries = Order.objects.filter(customer=self.customer_id, creation_date__lte=end_date).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, creation_date__lte=end_date).count()
            elif end_date is None:
                all_entries = Order.objects.filter(customer=self.customer_id, creation_date__gte=start_date).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, creation_date__gte=start_date).count()
            else:
                all_entries = Order.objects.filter(customer=self.customer_id, creation_date__gte=start_date,  creation_date__lte=end_date).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, creation_date__gte=start_date,  creation_date__lte=end_date).count()

        else:
            return Response(
                serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        next_page, previous_page = Paginator.pagination(count, limit, offset, request.path, request.query_params)
        orders = [{'order_id': entry.order_id, 'customer_id': entry.customer_id, 'creation_date': entry.creation_date, 'delivery_address': entry.delivery_address, 'total': entry.total, 'products': self.get_order_details(entry.order_id)} for entry in all_entries]

        return Response({'count': count, 'next': next_page, 'previous': previous_page, 'results': orders})

    
    def post(self, request, customer_id):

        self.customer_id = customer_id
        self.customer = Customer.objects.filter(customer_id=self.customer_id).get()

        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():

            quantity = 0
            total = 0
            products = []
            for (key, item) in enumerate(request.data['products']):
                
                serializerProducts = self.serializerProducts_class(data=item)

                if not serializerProducts.is_valid():
                    localErrors = {}
                    localErrors['products'] = {key: serializerProducts.errors.copy()}
                    return Response(
                        localErrors,
                        status = status.HTTP_400_BAD_REQUEST
                    )
                
                productId = serializerProducts.validated_data.get('product_id')
                check, product = self.customer_product_check(productId)

                if not check:
                    localErrors = {}
                    localErrors['products'] = [{key: [exceptions.ErrorDetail(string=f'The customer is not allowed to purchase the product identified by product_id {productId}', code='empty')]}]
                    return Response(
                        localErrors,
                        status = status.HTTP_409_CONFLICT
                    )

                total += serializerProducts.validated_data.get('quantity')*product.price
                quantity += serializerProducts.validated_data.get('quantity')

                if quantity>5:
                    localErrors = {}
                    localErrors['products'] = [exceptions.ErrorDetail(string='The total quantity of products cannot exceed 5.', code='empty')]
                    return Response(
                        localErrors,
                        status = status.HTTP_409_CONFLICT
                    )
                
                product.quantity = serializerProducts.validated_data.get('quantity')

                product_re = list(filter(lambda x: (x.product_id==product.product_id), products))
                if not len(product_re):
                    products.append(product)
                else:
                    product_re[0].quantity += product.quantity

            self.products = products[:]
            self.deliveryAddress = request.data['delivery_address']
            self.total = total

            self.set_products()

            order = {'order_id': self.order.order_id, 'customer_id': self.order.customer.customer_id, 'creation_date': self.order.creation_date, 'delivery_address': self.order.delivery_address, 'total': self.order.total, 'products': self.get_order_details(self.order.order_id)}

            return Response(order, status = status.HTTP_201_CREATED)
        else:
            return Response(
                serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

    
    def customer_product_check(self, productId):

        all_entries = CustomerProduct.objects.select_related('product').filter(customer=self.customer_id, product=productId)

        if all_entries.count() == 1:
            product = all_entries.all()[0].product
            return True, product
        
        return False, None
    
    def set_products(self):
        
        self.order = Order(customer=self.customer, creation_date=datetime.date.today(), delivery_address=self.deliveryAddress, total=self.total)

        self.order.save()

        self.order_details = []
        for item in self.products:

            order_detail = OrderDetail(order=self.order, product_description=item.product_description, price=item.price, product=item, quantity=item.quantity)

            order_detail.save()

            self.order_details.append(order_detail)
    
    def get_order_details(self, order_id):

        all_entries = OrderDetail.objects.select_related('product').filter(order=order_id).all()

        order_details = [{'product_id': order_detail.product.product_id, 'name': order_detail.product.name, 'quantity': order_detail.quantity} for order_detail in all_entries]

        return order_details



class CustomerOrdersView(APIView):

    serializer_class = serializers.OrdersSerializer
    serializerProducts_class = serializers.OrdersProductsSerializer
    serializerCustomerOrders_class = serializers.CustomerOrdersSerializer

    def get(self, request, customer_id, order_id, format=None):
            
        self.customer_id = customer_id

        serializer = self.serializerCustomerOrders_class(data=request.query_params)

        if serializer.is_valid():
            start_date = serializer.validated_data.get('start_date')
            end_date = serializer.validated_data.get('end_date')

            limit = serializer.validated_data.get('limit')
            offset = serializer.validated_data.get('offset')

            if (start_date is None and end_date is None) :
                all_entries = Order.objects.filter(customer=self.customer_id, order_id=order_id).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, order_id=order_id).count()
            elif start_date is None:
                all_entries = Order.objects.filter(customer=self.customer_id, order_id=order_id, creation_date__lte=end_date).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, order_id=order_id, creation_date__lte=end_date).count()
            elif end_date is None:
                all_entries = Order.objects.filter(customer=self.customer_id, order_id=order_id, creation_date__gte=start_date).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, order_id=order_id, creation_date__gte=start_date).count()
            else:
                all_entries = Order.objects.filter(customer=self.customer_id, order_id=order_id, creation_date__gte=start_date,  creation_date__lte=end_date).all()[offset:limit+offset]
                count = Order.objects.filter(customer=self.customer_id, order_id=order_id, creation_date__gte=start_date,  creation_date__lte=end_date).count()

        else:
            return Response(
                serializer.errors,
                status = status.HTTP_400_BAD_REQUEST
            )

        next_page, previous_page = Paginator.pagination(count, limit, offset, request.path, request.query_params)
        orders = [{'order_id': entry.order_id, 'customer_id': entry.customer_id, 'creation_date': entry.creation_date, 'delivery_address': entry.delivery_address, 'total': entry.total, 'products': self.get_order_details(entry.order_id)} for entry in all_entries]

        return Response({'count': count, 'next': next_page, 'previous': previous_page, 'results': orders})
    
    def get_order_details(self, order_id):

        all_entries = OrderDetail.objects.select_related('product').filter(order=order_id).all()

        order_details = [{'product_id': order_detail.product.product_id, 'name': order_detail.product.name, 'quantity': order_detail.quantity} for order_detail in all_entries]

        return order_details