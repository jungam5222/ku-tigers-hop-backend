from django.contrib import admin
from .models import Reservation, Table, Order, OrderItem, Menu

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'reservation_count', 'assigned_table', 'created_at')
    list_filter = ('assigned_table',)

@admin.register(Table)
class TableAdmin(admin.ModelAdmin):
    list_display = ('number', )

@admin.register(Order)
class TableAdmin(admin.ModelAdmin):
    list_display = ('reservation', 'price', 'is_paid')

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'quantity', 'price', 'order')

@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'serving', 'img')