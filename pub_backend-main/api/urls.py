from django.urls import path
from . import views

urlpatterns = [
    path('reservation/', views.create_reservation, name='create_reservation'),
    path('menu-items/', views.add_menu_items, name='add_menu_items'),
    path('manage/tables/', views.table_management, name='table_management'),
    path('manage/orders/', views.order_list, name='order_list'),
    path('manage/order-items/', views.order_item_list, name='order_item_list'),
    path('api/send-pay-message/<int:order_id>/', views.send_pay_message, name='send_pay_message'),
    path('api/toggle-paid-status/<int:order_id>/', views.toggle_paid_status, name='toggle_paid_status'),
    path('api/save-order-memo/<int:order_id>/', views.save_order_memo, name='save_order_memo'),
    path('api/menu/', views.get_menu, name='get_menu'),
    path('api/toggle-finish-status/<int:item_id>/', views.toggle_finish_status, name='toggle_finish_status'),
    path('api/waiting-queue/', views.get_waiting_queue, name='get_waiting_queue'),
    path('api/table/<str:table_number>/', views.get_table_reservation, name='get_table_reservation'),
    path('manage/summary/', views.order_summary, name='order_summary'),
]