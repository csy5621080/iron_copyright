from ninja import Router
from .models import Order, OrderStatus
order_api = Router()


@order_api.get("/undetermined_order/", auth=None, response=None)
def undetermined_order(request, order_num: str):
    order = Order.objects.filter(order_num=order_num)
    if order.exists():
        order.update(status=OrderStatus.Undetermined)
    return
