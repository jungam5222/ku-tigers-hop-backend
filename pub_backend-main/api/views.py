from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import render, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.db.models import IntegerField, Min, Count, Sum
from django.db.models.functions import Cast
from collections import defaultdict
from django.http import JsonResponse
from .models import Reservation, Table, Order, OrderItem, Menu
from .utils.solapi import send_sms
from datetime import timedelta


@api_view(['POST'])
def create_reservation(request):
    data = request.data

    try:
        reservation = Reservation.objects.create(
            name=data['name'],
            phone=data['phone'],
            reservation_count=data['reservation_count'],
            time=data['duration'],
        )

        order = Order.objects.create(is_paid=False, reservation=reservation)  # Link the order to the reservation

        for item in data['items']:
            if item['name'] == "흑백 세트 A":
                for _ in range(item['quantity']):
                    OrderItem.objects.create(
                        order=order,
                        name="나야, 짜치대패(세트A)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=18000
                    )
                    OrderItem.objects.create(
                        order=order,
                        name="이븐하게 익은 소시지(세트A)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=9000
                    )
            elif item['name'] == "흑백 세트 B":
                for _ in range(item['quantity']):
                    OrderItem.objects.create(
                        order=order,
                        name="비빔비빔 골뱅이소면(세트B)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=18000
                    )
                    OrderItem.objects.create(
                        order=order,
                        name="무..물코기(세트B)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=17000
                    )
            else:
                for _ in range(item['quantity']):  # Create multiple OrderItems for quantity > 1
                    OrderItem.objects.create(
                        order=order,
                        name=item['name'],
                        quantity=1,  # Each OrderItem has quantity 1
                        price=item['price']
                    )
        OrderItem.objects.create(
            order=order,
            name="테이블비",
            quantity=1,
            price=5000,
            finish=True
        )
        order.set_price()  # Set the price after adding items

        result = send_sms(reservation.phone, '''[ 백구회 일일호프 예약 안내 ]
컴퓨터학과 주점 대기자 명단에 등록되었음을 알려드립니다.
자리가 발생하는 경우 기재하신 번호로 연락드릴 예정입니다. 전화를 받지 않으실 경우, 다음 대기자에게 순번이 넘어갈 수 있으니 유의하여 주시기 바랍니다.
감사합니다.''')
        print(result)

        return Response({"message": "Reservation created successfully", "reservation_id": reservation.id}, status=status.HTTP_201_CREATED)

    except Exception as e:
        print(e)
        return Response({"message": "Error creating reservation"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def add_menu_items(request):
    data = request.data

    try:
        table_no = data['table_no']
        table = Table.objects.get(number=table_no)
        reservation = table.reservation
        
        if not reservation:
            return Response({"message": "No reservation assigned to this table."}, status=status.HTTP_400_BAD_REQUEST)

        # Always create a new order for the reservation
        order = Order.objects.create(is_paid=False, reservation=reservation)  # Link the new order to the reservation
        current_time = timezone.now()

        for item in data['items']:
            if item['name'] == "흑백 세트 A":
                for _ in range(item['quantity']):
                    OrderItem.objects.create(
                        order=order,
                        name="나야, 짜치대패(세트A)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=18000,
                        order_start_time=current_time  # Set order_start_time for newly added items
                    )
                    OrderItem.objects.create(
                        order=order,
                        name="이븐하게 익은 소시지(세트A)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=9000,
                        order_start_time=current_time  # Set order_start_time for newly added items
                    )
            elif item['name'] == "흑백 세트 B":
                for _ in range(item['quantity']):
                    OrderItem.objects.create(
                        order=order,
                        name="비빔비빔 골뱅이소면(세트B)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=18000,
                        order_start_time=current_time  # Set order_start_time for newly added items
                    )
                    OrderItem.objects.create(
                        order=order,
                        name="무..물코기(세트B)",
                        quantity=1,  # Each OrderItem has quantity 1
                        price=17000,
                        order_start_time=current_time  # Set order_start_time for newly added items
                    )
            else:
                for _ in range(item['quantity']):  # Create multiple OrderItems for quantity > 1
                    OrderItem.objects.create(
                        order=order,
                        name=item['name'],
                        quantity=1,  # Each OrderItem has quantity 1
                        price=item['price'],
                        order_start_time=current_time  # Set order_start_time for newly added items
                    )

        order.set_price()  # Set the price after adding items

        # Group items by name for the message
        grouped_items = defaultdict(lambda: {'quantity': 0, 'total_price': 0})
        for item in order.order_items.all():
            grouped_items[item.name]['quantity'] += item.quantity
            grouped_items[item.name]['total_price'] += item.total_price()

        # Generate the additional order message
        item_lines = [
            f"{name} (×{details['quantity']})\n - {details['total_price']}원"
            for name, details in grouped_items.items()
        ]
        total_price = order.price

        message = f"""[ 백구회 일일호프 추가 주문 안내 ]
컴퓨터학과 주점 추가 주문이 완료되었습니다.

{chr(10).join(item_lines)}

총액: {total_price}원
계좌번호: 토스뱅크 1000-4108-1382 김한성

3분 이내에 입금이 확인되지 않는 경우 주문이 취소될 수 있으니 유의 바랍니다.
본인이 주문하지 않았거나, 문의사항이 있는 경우 회신 바랍니다."""

        result = send_sms(reservation.phone, message)
        print(result)
        order.pay_message_sent = True
        order.save()
        
        return Response({
            "message": "Menu items added successfully",
            "order_id": order.id,
        }, status=status.HTTP_201_CREATED)

    except Table.DoesNotExist:
        return Response({"message": "Table not found."}, status=status.HTTP_404_NOT_FOUND)

    except Exception as e:
        print(e)
        return Response({"message": "Error adding menu items."}, status=status.HTTP_400_BAD_REQUEST)

def table_management(request):
    if request.method == 'POST':
        if 'assign' in request.POST:
            tid = request.POST.get('table_id')
            rid = request.POST.get('reservation_id')
            table = Table.objects.get(id=tid)
            res = Reservation.objects.get(id=rid)
            res.assigned_table = table
            res.entry_time = timezone.now()
            memo = request.POST.get('memo')
            if memo is not None:
                res.memo = memo
            res.save()
            
            # Always check for OrderItems that need order_start_time set
            current_time = timezone.now()
            # Get all orders for this reservation
            orders = Order.objects.filter(reservation=res)
            # Update all OrderItems for these orders that don't have an order_start_time
            for order in orders:
                OrderItem.objects.filter(order=order, order_start_time__isnull=True).update(
                    order_start_time=current_time
                )
        elif 'release' in request.POST:
            table = Table.objects.get(id=request.POST.get('table_id'))
            res = getattr(table, 'reservation', None)
            if res:
                res.assigned_table = None
                res.completed = True
                memo = request.POST.get('memo')
                if memo is not None:
                    res.memo = memo
                res.save()
        elif 'resend' in request.POST:
            rid = request.POST.get('reservation_id')
            res = Reservation.objects.get(id=rid)
            opt = request.POST.get('time_option')
            if opt == 'original':
                # Keep the original created_at
                pass
            elif opt == 'now':
                res.created_at = timezone.now()
            elif opt == 'custom':
                custom_time = request.POST.get('custom_time')
                res.created_at = parse_datetime(custom_time)  # Parse custom datetime
            res.completed = False
            res.entry_time = None
            res.assigned_table = None
            memo = request.POST.get('memo')
            if memo is not None:
                res.memo = memo
            res.save()
        elif 'save_memo' in request.POST:               # 추가
            rid = request.POST.get('reservation_id')
            res = Reservation.objects.get(id=rid)
            res.memo = request.POST.get('memo', '')
            res.save()
        return redirect('table_management')

    tables = Table.objects.all().annotate(
        num=Cast('number', IntegerField())
    ).order_by('num')
    waiting = Reservation.objects.filter(
        assigned_table__isnull=True, completed=False
    ).order_by('created_at')
    completed_list = Reservation.objects.filter(
        completed=True
    ).order_by('-entry_time')
    return render(request, 'api/table_management.html', {
        'tables': tables,
        'waiting': waiting,
        'completed': completed_list,
    })

def group_order_items(order):
    grouped_items = defaultdict(lambda: {'quantity': 0, 'total_price': 0})
    for item in order.order_items.all():
        grouped_items[item.name]['quantity'] += item.quantity
        grouped_items[item.name]['total_price'] += item.quantity * item.price
    # Convert grouped_items to a list of dictionaries
    grouped_items_list = [{'name': name, 'quantity': details['quantity'], 'total_price': details['total_price']}
                          for name, details in grouped_items.items()]
    #print(f"Grouped items for order {order.id}: {grouped_items_list}")  # Debug statement
    return grouped_items_list

def get_order_number(order):
    """Return the order number for a reservation (1st, 2nd, etc.)"""
    if not order.reservation:
        return None
    
    reservation_orders = Order.objects.filter(
        reservation=order.reservation
    ).order_by('created_at')
    
    for i, o in enumerate(reservation_orders, 1):
        if o.id == order.id:
            return i
    return None

def order_list(request):
    # Categorize orders
    # For assigned_not_completed, we'll need to annotate and order separately
    assigned_not_completed_raw = Order.objects.filter(
        reservation__assigned_table__isnull=False,
        reservation__completed=False
    ).select_related('reservation__assigned_table')
    
    # Other categories remain the same
    unassigned_not_completed = Order.objects.filter(
        reservation__assigned_table__isnull=True,
        reservation__completed=False
    )
    assigned_completed = Order.objects.filter(
        reservation__assigned_table__isnull=False,
        reservation__completed=True
    )
    unassigned_completed = Order.objects.filter(
        reservation__assigned_table__isnull=True,
        reservation__completed=True
    )

    # Process assigned_not_completed with custom sorting
    assigned_not_completed_entries = []
    for order in assigned_not_completed_raw:
        table_number = order.reservation.assigned_table.number
        order_number = get_order_number(order)
        assigned_not_completed_entries.append({
            'order': order,
            'grouped_items': group_order_items(order),
            'order_number': order_number,
            'table_number': table_number,
        })
    
    # Sort by table number (as integer if possible) and then by order number
    def sort_key(entry):
        try:
            # Try to convert table number to integer for proper numeric sorting
            table_num = int(entry['table_number'])
        except ValueError:
            # If not possible, use the string
            table_num = entry['table_number']
        return (table_num, entry['order_number'] or 0)
    
    assigned_not_completed_entries.sort(key=sort_key)

    # Group order items for other categories
    categorized_orders = {
        'assigned_not_completed': assigned_not_completed_entries,
        'unassigned_not_completed': [
            {'order': order, 'grouped_items': group_order_items(order), 'order_number': get_order_number(order)}
            for order in unassigned_not_completed
        ],
        'assigned_completed': [
            {'order': order, 'grouped_items': group_order_items(order), 'order_number': get_order_number(order)}
            for order in assigned_completed
        ],
        'unassigned_completed': [
            {'order': order, 'grouped_items': group_order_items(order), 'order_number': get_order_number(order)}
            for order in unassigned_completed
        ],
    }

    return render(request, 'api/order_list.html', categorized_orders)

@api_view(['POST'])
def toggle_paid_status(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        order.is_paid = not order.is_paid
        order.save()
        return JsonResponse({
            "success": True, 
            "message": f"Order marked as {'paid' if order.is_paid else 'unpaid'}",
            "is_paid": order.is_paid
        })
    except Order.DoesNotExist:
        return JsonResponse({"success": False, "message": "Order not found."}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "message": "Failed to update payment status."}, status=500)

@api_view(['POST'])
def save_order_memo(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        memo = request.data.get('memo', '')
        
        if not order.reservation:
            return JsonResponse({"success": False, "message": "Order has no associated reservation."}, status=400)
        
        order.reservation.memo = memo
        order.reservation.save()
        
        return JsonResponse({"success": True, "message": "Memo saved successfully."})
    except Order.DoesNotExist:
        return JsonResponse({"success": False, "message": "Order not found."}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "message": "Failed to save memo."}, status=500)

@api_view(['POST'])
def send_pay_message(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        reservation = order.reservation

        # Group items by name
        grouped_items = defaultdict(lambda: {'quantity': 0, 'total_price': 0})
        for item in order.order_items.all():
            grouped_items[item.name]['quantity'] += item.quantity
            grouped_items[item.name]['total_price'] += item.total_price()

        # Generate the payment message
        item_lines = [
            f"{name} (×{details['quantity']})\n - {details['total_price']}원"
            for name, details in grouped_items.items()
        ]
        total_price = order.price or order.calculate_total_price()
        message = f"""[ 백구회 일일호프 결제 안내 ]
컴퓨터학과 주점 결제 안내입니다. 3분 이내에 입금이 확인되지 않는 경우 주문이 취소될 수 있으니 유의 바랍니다.

{chr(10).join(item_lines)}

총액: {total_price}원
계좌번호: 토스뱅크 100041081382 김한성

본인이 주문하지 않았거나, 문의사항이 있는 경우 회신 바랍니다."""

        if order.pay_message_sent:
            # Resend confirmation logic
            response_message = f"Payment message resent to {reservation.phone}."
        else:
            # Send the message for the first time
            response_message = f"Payment message sent to {reservation.phone}."
            order.pay_message_sent = True
            order.save()

        # Simulate sending the message (replace with actual SMS logic)
        result = send_sms(reservation.phone, message)
        print(result)

        return JsonResponse({"success": True, "message": response_message})
    except Order.DoesNotExist:
        return JsonResponse({"success": False, "message": "Order not found."}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "message": "Failed to send the message."}, status=500)

@api_view(['GET'])
def get_menu(request):
    """
    Get all menu items that are currently being served (serving=True)
    """
    try:
        menu_items = Menu.objects.filter(serving=True)
        menu_data = [
            {
                'id': item.id,
                'name': item.name,
                'description': item.description,
                'price': item.price,
                'imageName': item.img 
            }
            for item in menu_items
        ]
        return Response(menu_data, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response({"message": "Error fetching menu items"}, status=status.HTTP_400_BAD_REQUEST)

def order_item_list(request):
    # Get all unfinished items for active tables, ordered by order_start_time
    # Only include items from PAID orders
    unfinished_items = OrderItem.objects.filter(
        finish=False,
        order__is_paid=True,  # Only show items from paid orders
        order__reservation__assigned_table__isnull=False,
        order__reservation__completed=False
    ).select_related('order__reservation__assigned_table').order_by('order_start_time')
    
    # Get all finished items for active tables, also only from PAID orders
    finished_items = OrderItem.objects.filter(
        finish=True,
        order__is_paid=True,  # Only show items from paid orders
        order__reservation__assigned_table__isnull=False,
        order__reservation__completed=False
    ).select_related('order__reservation__assigned_table')
    
    # Create a summary of unfinished items grouped by menu name
    # Now only includes items from paid orders
    menu_summary = {}
    for item in unfinished_items:
        if item.name in menu_summary:
            menu_summary[item.name]['count'] += item.quantity
        else:
            menu_summary[item.name] = {
                'count': item.quantity,
                'price': item.price
            }
    
    # Convert to list for template rendering
    menu_summary_list = [{'name': name, 'count': data['count'], 'price': data['price']} 
                         for name, data in menu_summary.items()]
    
    return render(request, 'api/order_item_list.html', {
        'unfinished_items': unfinished_items,
        'finished_items': finished_items,
        'menu_summary': menu_summary_list,
    })

@api_view(['POST'])
def toggle_finish_status(request, item_id):
    try:
        item = OrderItem.objects.get(id=item_id)
        item.finish = not item.finish
        item.save()
        return JsonResponse({
            "success": True, 
            "message": f"Item marked as {'finished' if item.finish else 'unfinished'}",
            "is_finished": item.finish
        })
    except OrderItem.DoesNotExist:
        return JsonResponse({"success": False, "message": "Item not found."}, status=404)
    except Exception as e:
        print(e)
        return JsonResponse({"success": False, "message": "Failed to update status."}, status=500)

@api_view(['GET'])
def get_waiting_queue(request):
    """
    Returns information about the current waiting queue and estimated waiting time.
    """
    try:
        # Current time
        current_time = timezone.now()
        
        # Get the waiting queue (reservations not assigned to a table and not completed)
        waiting_queue = list(Reservation.objects.filter(
            assigned_table__isnull=True, 
            completed=False
        ).order_by('created_at'))
        
        # Get all tables and calculate when each will be free
        table_free_times = []
        for table in Table.objects.all():
            if hasattr(table, 'reservation') and table.reservation:
                # If table has a reservation
                res = table.reservation
                # Calculate expected exit time
                if res.exit_time:
                    # Use the reservation's exit time (entry_time + time)
                    free_time = res.exit_time + timedelta(minutes=5)  # Add 5 min turnover
                else:
                    # No exit time available, use a default estimate
                    free_time = current_time + timedelta(minutes=65)  # 60 min + 5 min turnover
            else:
                # Table is currently free
                free_time = current_time
            
            table_free_times.append(free_time)
        
        # Sort tables by when they'll be free
        table_free_times.sort()
        
        # Simulate assigning tables to waiting reservations
        queue_info = []
        simulation_table_times = table_free_times.copy()
        
        for i, res in enumerate(waiting_queue):
            if simulation_table_times:
                # Get the next available table
                next_free_time = simulation_table_times[0]
                
                # Calculate wait time for this reservation
                wait_time = (next_free_time - current_time).total_seconds() / 60
                expected_seating = next_free_time
                
                # Remove this table and add it back with updated free time
                simulation_table_times.pop(0)
                new_free_time = expected_seating + timedelta(minutes=res.time + 5)
                simulation_table_times.append(new_free_time)
                
                # Resort the table free times for the next reservation
                simulation_table_times.sort()
            else:
                # No tables available (shouldn't happen unless there are no tables)
                wait_time = 0
                expected_seating = current_time
            
            queue_info.append({
                'position': i + 1,
                'name': res.name,
                'party_size': res.reservation_count,
                'waiting_since': res.created_at.isoformat(),
                'estimated_wait_minutes': max(0, round(wait_time))
            })
        
        # Calculate estimated wait for a new reservation
        estimated_wait_for_new = 0
        if simulation_table_times:
            # A new reservation would get the next available table
            estimated_wait_for_new = (simulation_table_times[0] - current_time).total_seconds() / 60
        
        estimated_wait_for_new = estimated_wait_for_new//2

        response_data = {
            'queue_length': len(waiting_queue),
            'estimated_wait_minutes': max(0, round(estimated_wait_for_new)),
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    except Exception as e:
        print(e)
        return Response({"message": "Error retrieving queue information"}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_table_reservation(request, table_number):
    """
    Get the name of the person assigned to a specific table.
    """
    try:
        table = Table.objects.get(number=table_number)
        
        if hasattr(table, 'reservation') and table.reservation:
            return Response({
                "table_number": table_number,
                "has_reservation": True,
                "name": table.reservation.name,
                "reservation_count": table.reservation.reservation_count
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "table_number": table_number,
                "has_reservation": False,
                "message": "No reservation assigned to this table."
            }, status=status.HTTP_200_OK)
            
    except Table.DoesNotExist:
        return Response({
            "message": f"Table with number {table_number} not found."
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(e)
        return Response({
            "message": "Error retrieving table information."
        }, status=status.HTTP_400_BAD_REQUEST)

def order_summary(request):
    # Get all paid orders
    paid_orders = Order.objects.filter(is_paid=True).select_related('reservation')
    
    # Find all unique menu item names across all order items
    all_menu_items = OrderItem.objects.values_list('name', flat=True).distinct().order_by('name')
    unique_menu_names = list(filter(lambda x: x != "테이블비", all_menu_items))
    
    # Prepare data for the summary table
    summary_data = []
    
    for order in paid_orders:
        # Skip orders without reservations
        if not order.reservation:
            continue
        
        # Get earliest order_start_time for sorting purposes
        earliest_time = OrderItem.objects.filter(
            order=order, 
            order_start_time__isnull=False
        ).aggregate(Min('order_start_time'))['order_start_time__min']
        
        if not earliest_time:
            # Skip orders without any order_start_time
            continue
        
        # Count menu items for this order
        menu_counts = {}
        for menu_name in unique_menu_names:
            count = OrderItem.objects.filter(
                order=order,
                name=menu_name
            ).aggregate(total=Sum('quantity'))['total'] or 0
            menu_counts[menu_name] = count
        
        # Add entry to summary data
        summary_data.append({
            'order': order,
            'reservation': order.reservation,
            'earliest_time': earliest_time,
            'menu_counts': menu_counts,
        })
    
    # Sort by earliest order_start_time
    summary_data.sort(key=lambda x: x['earliest_time'])
    
    return render(request, 'api/order_summary.html', {
        'summary_data': summary_data,
        'menu_names': unique_menu_names,
    })
