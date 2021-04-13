from django.urls import path
from store_api import views

urlpatterns = [
    path('customers', views.CustomersView.as_view()),
    path('customers/<int:customer_id>', views.CustomerView.as_view()),
    path('customers/<int:customer_id>/products', views.CustomerProductsView.as_view()),
    path('customers/<int:customer_id>/orders', views.CustomerOrdersView.as_view()),
    path('customers/<int:customer_id>/orders/<int:order_id>', views.CustomerOrderView.as_view())
]