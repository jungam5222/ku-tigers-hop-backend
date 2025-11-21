from django.db import models
from datetime import timedelta

class Reservation(models.Model):
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    reservation_count = models.IntegerField()
    time = models.IntegerField(default=60)
    created_at = models.DateTimeField(auto_now_add=True)
    memo = models.TextField(blank=True)  # 추가
    entry_time = models.DateTimeField(null=True, blank=True)
    completed = models.BooleanField(default=False)
    assigned_table = models.OneToOneField('Table', null=True, blank=True, on_delete=models.SET_NULL, related_name='reservation')
    
    @property
    def exit_time(self):
        if self.entry_time:
            return self.entry_time + timedelta(minutes=self.time)
        return None

    def __str__(self):
        return f'{self.name} ({self.phone})'

class Order(models.Model):
    reservation = models.ForeignKey('Reservation', null=True, blank=True, on_delete=models.CASCADE, related_name='orders')
    is_paid = models.BooleanField(default=False)
    price = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    pay_message_sent = models.BooleanField(default=False)

    def calculate_total_price(self):
        return sum(item.total_price() for item in self.order_items.all())

    def set_price(self):
        self.price = self.calculate_total_price()
        self.save()

    def __str__(self):
        return f'Order (Paid: {self.is_paid})'

class Table(models.Model):
    number = models.CharField(max_length=10, unique=True)
    
    def __str__(self):
        return f'Table {self.number}'

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='order_items')
    name = models.CharField(max_length=200)
    quantity = models.IntegerField()
    price = models.IntegerField()
    finish = models.BooleanField(default=False)
    order_start_time = models.DateTimeField(null=True, blank=True)

    def total_price(self):
        return self.quantity * self.price

    def __str__(self):
        return f'{self.name} x {self.quantity}'

class Menu(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.IntegerField()
    serving = models.BooleanField(default=True)
    img = models.CharField(blank=True, null=True, max_length=100)
