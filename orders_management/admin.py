import csv
from datetime import datetime
from threading import Thread

from annoying.functions import get_object_or_None
from django import forms
from django.db import transaction
from django.contrib import admin
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Q, Max
from django.db.models.functions import TruncDate
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.urls import path
from django.utils.safestring import mark_safe
from django.utils.timezone import now

from authentication.utils import SendEmailViewMixin
from categories.admin import my_admin_site
from categories.models import Categories
from categories.utils import float_to_rupee
from offers_management.utils import code_coupon
from orders_management import models, utils
from orders_management.Shipping_details import order_shipment, update_tracking_link
from orders_management.utils import calculate_amount, id_to_cart_user, int_to_order
from django_admin_listfilter_dropdown.filters import RelatedDropdownFilter


class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

    def clean(self):
        if not (self.cleaned_data['csv_file'] or self.cleaned_data['csv_file'].endswith(".csv")):
            raise forms.ValidationError(
                'Please enter your code in text box or upload an appropriate file.')
        return self.cleaned_data


class OrderStatusAdminInline(admin.StackedInline):
    model = models.OrderStatus
    fields = ("name", "is_active")


@admin.register(models.OrderStatusMaster, site=my_admin_site)
class OrderStatusMasterAdmin(admin.ModelAdmin):
    list_display = ("id", "name")

    def has_delete_permission(self, request, obj=None):
        return False


class Transaction(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "Transaction"
        verbose_name_plural = "1. Transaction"


class OrderPlaced(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "Order Placed"
        verbose_name_plural = "2. Order Placed"


class ReadyForDispatch(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "Ready To Ship"
        verbose_name_plural = "3. Ready To Ship"


class Dispatch(models.Orders):
    class Meta:
        proxy = True
        verbose_name = " Shipped"
        verbose_name_plural = "4. Shipped"


class Delivered(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "Delivered"


class CancelPlaced(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "Canceled Order"
        verbose_name_plural = "6. Canceled Order"


class ReturnedOrder(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "Returned Order"
        verbose_name_plural = "7. Returned Order"


class AllOrder(models.Orders):
    class Meta:
        proxy = True
        verbose_name = "All Order"
        verbose_name_plural = "8. All Orders"


@admin.register(models.InfluencerOrder, site=my_admin_site)
class InfluencerOrderAdmin(admin.ModelAdmin):
    list_display = ("id", "affiliates", "product", "status", "created_on")
    search_fields = ("id", "affiliates__user__username", "product__title")
    list_filter = ("product",)
    date_hierarchy = "created_on"

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class OrderedItemsAdminInline(admin.StackedInline):
    model = models.OrderItems
    readonly_fields = ("pay_amount",)
    fields = (
        ("product", "quantity", "currency", "offer_title", "unit_price", "offer_amount", "pay_amount", "color", "gst"),)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def pay_amount(self, obj):
        return round((obj.unit_price * obj.quantity) - obj.offer_amount, 2)


@admin.register(Transaction, OrderPlaced, CancelPlaced, ReadyForDispatch, ReturnedOrder, Delivered, Dispatch, AllOrder,
                site=my_admin_site)
class OrdersAdmin(admin.ModelAdmin, SendEmailViewMixin):
    list_display_links = ("tracking_client_id", "user", "customer_info", "address_detail", "payment_type",
                          "payment_status", "currency_type", "total_amount", "pay_amount", "coupon_amount",
                          "shipping_charge", "cod_charge", "coupon",)
    date_hierarchy = "created_on"
    search_fields = ("tracking_client_id", "currency_type", "coupon__offer_code", "user__user__first_name",
                     "user__user__username", "user__user__email", "transaction_id")
    list_filter = ("payment_status", "payment_type", "currency_type", ("status", RelatedDropdownFilter),
                   ("coupon", RelatedDropdownFilter))
    change_form_template = "admin/order-details.html"
    change_list_template = "order_list_template.html"

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        _object = int_to_order(object_id)
        extra_context['object'] = _object

        is_edit = True if _object.is_amount_refunded != True \
            and _object.status.order_status.id in [1, 2] and _object.order_items.count() > 1 else False
        extra_context['is_edit'] = is_edit
        extra_context['payment_gateway'] = models.PaymentGateWay.objects.filter(
            is_active=True)
        return super(OrdersAdmin, self).change_view(request, object_id, form_url, extra_context=extra_context)

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['payment_gateway'] = models.PaymentGateWay.objects.filter(
            is_active=True)
        return super(OrdersAdmin, self).changelist_view(request, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "status":

            if self.model.__name__ == "Transaction":
                kwargs["queryset"] = models.OrderStatus.objects.filter(
                    order_status=1)
            elif self.model.__name__ == "OrderPlaced":
                kwargs['queryset'] = models.OrderStatus.objects.filter(
                    order_status=1)
            elif self.model.__name__ == "ReadyForDispatch":
                kwargs['queryset'] = models.OrderStatus.objects.filter(
                    order_status=2)
            elif self.model.__name__ == "Dispatch":
                kwargs['queryset'] = models.OrderStatus.objects.filter(
                    order_status=3)
            elif self.model.__name__ == "Delivered":
                kwargs['queryset'] = models.OrderStatus.objects.filter(
                    order_status=4)
            elif self.model.__name__ == "CancelPlaced":
                kwargs['queryset'] = models.OrderStatus.objects.filter(
                    order_status=5)
            elif self.model.__name__ == "ReturnedOrder":
                kwargs['queryset'] = models.OrderStatus.objects.filter(
                    order_status=6)

        return super(OrdersAdmin, self).formfield_for_foreignkey(db_field, request, **kwargs)

    def get_queryset(self, request):
        qs = super(OrdersAdmin, self).get_queryset(request)
        if self.model.__name__ == "Transaction":
            return qs.filter(is_success=False, status=1)
        elif self.model.__name__ == "OrderPlaced":
            return qs.filter(is_success=True, status__order_status=1)
        elif self.model.__name__ == "ReadyForDispatch":
            return qs.filter(is_success=True, status__order_status=2)
        elif self.model.__name__ == "Dispatch":
            return qs.filter(is_success=True, status__order_status=3)
        elif self.model.__name__ == "Delivered":
            return qs.filter(is_success=True, status__order_status=4)
        elif self.model.__name__ == "CancelPlaced":
            return qs.filter(is_success=True, status__order_status=5)
        elif self.model.__name__ == "ReturnedOrder":
            return qs.filter(is_success=True, status__order_status=6)
        elif self.model.__name__ == "AllOrder":
            return qs.filter(is_success=True)
        else:
            return qs

    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('<path:object_id>/change/<int:pk>/delete-item/',
                 self.delete_order_item),
            path('import-csv/', self.import_csv),
            path('transaction-update/', self.transaction_update),
            path('move_order_cod/<int:pk>/', self.move_order),
            path('move_order_payment/<int:pk>/', self.move_payment),
            path('cancel_order/<int:pk>/', self.cancel_order),
            path('download_orders/<int:pk>/', self.download_orders),
            path('download-orders-report/', self.download_daily_order),
            path('orders-report/', self.order_report),
            path('sync-tracking/<int:pk>', self.sync_tracking),
            path('download_report/', self.download_report),
            path('download_order_shipping/', self.download_order_shipping),
            path('update_order_shipping/', self.update_order_shipping),
        ]
        return my_urls + urls

    fieldsets = (
        ('Basic info', {
            'fields': (("tracking_client_id", "user"), ('name', "email", "dial_code", "phone"), "address_detail",
                       "status", "created_on")
        }),


    )

    @staticmethod
    def import_csv(request):

        if request.method == "POST":
            now = datetime.now()
            order_dict = dict()
            try:
                object_id = models.Orders.objects.latest(
                    "id").id if models.Orders.objects.latest("id") else 0
            except:
                object_id = 0
            tracking_client_id = "S&B-{}-{:04d}".format(
                now.strftime("%d%m"), object_id + 1)
            try:
                user = models.UserProfile.objects.get(
                    user__username=request.POST['username'])
            except:
                dial_code = models.Countries.objects.get(
                    id=request.POST['dial_code'])
                primary_user = User.objects.create_user(username=request.POST['username'],
                                                        first_name=request.POST['first_name'],
                                                        email=request.POST['email'])
                user = models.UserProfile.objects.create(
                    user=primary_user, country=dial_code)

            country = models.Countries.objects.get(id=request.POST['country'])
            address = models.Address.objects.create(user=user, door_no=request.POST['door_no'],
                                                    street_address=request.POST['street_address'],
                                                    city=request.POST['city'],
                                                    state=request.POST['state'],
                                                    locality=request.POST['locality'],
                                                    landmark=request.POST['landmark'], country=country,
                                                    postal_code=request.POST['postal_code'], address_type="Home")
            coupon = None
            if "coupon_code" in request.POST and request.POST['coupon_code']:
                coupon = code_coupon(request.POST['coupon_code'])
                order_dict['coupon'] = coupon
                order_dict['coupon_code'] = request.POST['coupon_code']

            order_dict['user'] = user
            order_dict['tracking_client_id'] = tracking_client_id
            order_dict['address'] = address
            order_dict['currency_type'] = country.currency_type
            order_dict['name'] = user.user.get_full_name()
            order_dict['email'] = user.user.email
            order_dict['phone'] = user.user.username
            if request.POST.get("pay_mode", None):
                order_dict['pay_mode_id'] = request.POST.get("pay_mode", None)

            order = models.Orders.objects.create(**order_dict)
            for product in ["product_3", "product_4", "product_1", "product_2"]:
                if product in request.POST and int(request.POST[product]) >= 1:
                    id_to_cart_user(user, int(product.replace(
                        "product_", "")), int(request.POST[product]))

            checkout_amount = calculate_amount(user, order, country=address.country, offer=coupon,
                                               is_wallet=False)

            order.total_amount = checkout_amount['total_amount']
            order.coupon_amount = checkout_amount['coupon_amount']
            order.pay_amount = checkout_amount['pay_amount']
            order.shipping_charge = checkout_amount['shipping_charge']
            order.cod_charge = checkout_amount['cod_charge']
            order.other_charge = checkout_amount['other_charge']
            order.other_charge = checkout_amount['other_charge']
            order.payment_status = True
            order.is_success = True
            order.save()
            return redirect("..")

        payload = {"products": models.Products.objects.filter(category__in=[1]),
                   "pay_modes": models.PaymentGateWay.objects.filter(is_active=True),
                   "country": models.Countries.objects.filter(is_active=True)}
        return render(request, "order.html", payload)

    def address_detail(self, obj):
        return mark_safe("{door_no}, {street_address}<br>{city}<br>{state}<br>{country}-"
                         "{postal_code}".format(door_no=obj.address.door_no, street_address=obj.address.street_address,
                                                city=obj.address.city, locality=obj.address.locality,
                                                state=obj.address.state,
                                                country=obj.address.country, postal_code=obj.address.postal_code))

    address_detail.short_description = "Address"

    def get_list_display(self, request):
        if self.model.__name__ == "Transaction":
            return ("order_info", "customer_info", "address_detail", "status", "payment_type",
                    "payment_status", "currency_type", "total_amount", "pay_amount", "coupon_amount", "shipping_charge",
                    "transaction_id", "move_cod", "pay_mode")
        if self.model.__name__ == "OrderPlaced":
            return ("order_info", "customer_info", "address_detail", "status", "payment_type",
                    "payment_status", "currency_type", "total_amount", "pay_amount", "coupon_amount", "shipping_charge",
                    "cod_charge", "pay_mode", "cancel")

        return ("order_info", "customer_info", "address_detail", "status", "payment_type",
                "payment_status", "currency_type", "total_amount", "pay_amount", "coupon_amount", "shipping_charge",
                "cod_charge", "coupon", "pay_mode", "track_link")

    def has_delete_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False

    @transaction.atomic()
    def delete_order_item(self, request, pk, **kwargs):
        if not request.user.is_authenticated:
            return redirect('/')

        item = models.OrderItems.objects.get(pk=pk)
        models.OrderItemsCancelled.objects.create(order=item.order, product=item.product, product_sku=item.product_sku,
                                                  quantity=item.quantity, offer_title=item.offer_title,
                                                  offer_amount=item.offer_amount, currency=item.currency,
                                                  unit_price=item.unit_price, gst=item.gst, color=item.color)

        order = item.order

        item_amount = round(item.unit_price * item.quantity,
                            2) - item.offer_amount
        item_gst = item.gst

        order.total_amount = round(order.total_amount - item_amount, 2)
        order.total_gst = round(order.total_gst - item_gst, 2)
        order.pay_amount = round(
            order.pay_amount - (item_gst + item_amount), 2)

        if order.payment_status:
            order.refund_amount = round(item_gst + item_amount, 2)
            order.is_amount_refunded = False

        order.save()

        item.delete()

        return redirect("../..")

    def move_order(self, request, pk):
        if not request.user.is_authenticated:
            return redirect('/')
        if not request.user.check_password(request.POST['password']):
            return redirect('/')
        order = int_to_order(pk)
        order.is_success = True
        order.payment_type = "COD"
        order.cod_charge = order.address.country.cod_charge
        order.save()
        self.sms_context = {"order": order}
        Thread(target=self.send_email, args=(
            order.user.user.email, self.sms_context,)).start()
        Thread(target=utils.push_notification, args=(1, order)).start()
        return redirect("../..")

    def move_payment(self, request, pk):

        if not request.user.is_authenticated:
            return redirect('/')
        if not request.user.check_password(request.POST['password']):
            return redirect('/')

        order = int_to_order(pk)
        payment_mode = models.PaymentGateWay.objects.get(
            id=request.POST['payment_mode'])
        order.is_success = True
        order.payment_status = True
        order.pay_mode = payment_mode
        order.save()
        self.sms_context = {"order": order}
        Thread(target=self.send_email, args=(
            order.user.user.email, self.sms_context,)).start()
        Thread(target=utils.push_notification, args=(1, order)).start()
        return redirect("../..")

    @staticmethod
    def cancel_order(request, pk):
        if not request.user.is_authenticated:
            return redirect('/')
        if not request.user.check_password(request.POST['password']):
            return redirect('/')
        order = int_to_order(pk)
        order.status = models.OrderStatus.objects.get(id=2)
        order.save()
        return redirect("../..")

    @staticmethod
    def move_cod(obj):
        return mark_safe("""<a class='btn btn-outline-secondary' onClick="comfirmModel(2, {id})"> Move Pay</a>
        <br><a class='btn btn-outline-secondary' onClick="comfirmModel(1, {id})"> Move COD</a>""".format(id=obj.id))

    @staticmethod
    def cancel(obj):
        return mark_safe(
            """<a class='btn btn-outline-secondary' onClick="comfirmModel(3, {id})">Cancel Order</a>""".format(
                id=obj.id))

    def order_info(self, obj):
        if self.model.__name__ == "CancelPlaced":
            return mark_safe(
                """{}<br>{}<br>{}""".format(obj.tracking_client_id, obj.created_on.time().strftime("%H:%M:%S"),
                                            obj.updated_on.strftime("%m/%d/%Y, %H:%M:%S")))
        return mark_safe("""{}<br><br>{}""".format(obj.tracking_client_id, obj.created_on.time().strftime("%H:%M:%S")))

    @staticmethod
    def customer_info(obj):
        return mark_safe("{}<br>{}<br>{}".format(obj.name, obj.email, obj.phone))

    @staticmethod
    def track_link(obj):
        if obj.track_url:
            return mark_safe("<a target='_blank' class='btn btn-outline-secondary' href={}> Tracking link </a>".format(
                obj.track_url))
        elif obj.awb_code and not obj.track_url:
            return mark_safe(
                "<a class='btn btn-outline-secondary' href=sync-tracking/{}> Sync Tracking </a>".format(
                    obj.id))
        return "---"

    @staticmethod
    def order_report(request):
        if not request.user.is_authenticated:
            return redirect('/')
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Report-{}.csv'.format(
            now().time())
        fieldnames = ['Date', 'Overall Failure Transaction',
                      'Overall Online Failure Transaction', 'Overall COD Failure Transaction',
                      'No of Failure Transaction',
                      'No of Online Failure Transaction', 'No of COD Failure Transaction', 'No of Success Transaction',
                      'No of Online Success Transaction', 'No of COD Success Transaction', 'Online Transaction',
                      'COD Transaction', 'Overall Transaction']

        writer = csv.DictWriter(response, fieldnames=fieldnames)
        writer.writeheader()
        orders = models.Orders.objects.filter(
            address__country=1).dates("created_on", "day", order="DESC")
        for order in orders:
            date_order = models.Orders.objects.filter(
                created_on__date=order).exclude(status__order_status=5)
            order_sum = date_order.aggregate(success_count=Count('id', filter=Q(is_success=True)),
                                             online_success=Count('id',
                                                                  filter=Q(is_success=True, payment_type="Online")),
                                             cod_success=Count('id', filter=Q(
                                                 is_success=True, payment_type="COD")),
                                             failure_count=Count(
                                                 'id', filter=Q(is_success=False)),
                                             online_failure=Count('id',
                                                                  filter=Q(is_success=False, payment_type="Online")),
                                             cod_failure=Count('id', filter=Q(
                                                 is_success=False, payment_type="COD")),
                                             online_sum=Sum("pay_amount",
                                                            filter=Q(payment_type="Online", is_success=True)),
                                             cod_sum=Sum("pay_amount", filter=Q(
                                                 payment_type="COD", is_success=True)),
                                             overall_sum=Sum("pay_amount", filter=Q(is_success=True)))

            failure_order_sum = date_order.filter(is_success=False).exclude(
                user__in=date_order.filter(is_success=True, created_on__date__year=order.year).values_list(
                    "user")).aggregate(failure_count=Count("id"),
                                       online_failure=Count('id', filter=Q(
                                           is_success=False, payment_type="Online")),
                                       cod_failure=Count('id', filter=Q(is_success=False, payment_type="COD")))

            writer.writerow({'Date': order, 'Online Transaction': float_to_rupee(order_sum['online_sum']),
                             'COD Transaction': float_to_rupee(order_sum['cod_sum']),
                             'Overall Transaction': float_to_rupee(order_sum['overall_sum']),

                             'No of Success Transaction': order_sum['success_count'],
                             'No of Online Success Transaction': order_sum['online_success'],
                             'No of COD Success Transaction': order_sum['cod_success'],

                             'No of COD Failure Transaction': failure_order_sum['cod_failure'],
                             'No of Online Failure Transaction': failure_order_sum['online_failure'],
                             'No of Failure Transaction': failure_order_sum['failure_count'],

                             "Overall Failure Transaction": order_sum['failure_count'],
                             'Overall COD Failure Transaction': order_sum['cod_failure'],
                             'Overall Online Failure Transaction': order_sum['online_failure'],
                             })

        return response

    @staticmethod
    def download_orders(request, pk):

        if not request.user.is_authenticated:
            return redirect('/')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Orders-{}.csv'.format(
            now().date())

        filter_dict = dict()
        for key, value in request.GET.items():
            filter_dict[key] = value

        queryset = models.Orders.objects.filter(status__order_status__in=[1, 2, 3, 4], is_success=True).filter(
            **filter_dict).order_by("-created_on")
        product_count = queryset.annotate(items_id=Count("order_items")).aggregate(
            max_item=Max("items_id"))['max_item']
        product_count = product_count if product_count and product_count > 0 else 1

        filed_names = ["S.No", "Invoice Date", "Invoice Number", "Customer Name", "Customer Email", "Customer Mobile",
                       "Customer Address", "Purchase Order No", "Customer GST Number", "Payment Terms"]
        filed_names_2 = ["Total", "Subtotal", "Other Charges",  "Other Charges CGST", "Other Charges SGST", "Discount",
                         "Gross", "CGST", "SGST", "Net"]

        for product_head in range(1, product_count + 1):
            filed_names.extend(["Product {}".format(product_head), "Product {} Qty".format(product_head),
                                "Product {} Rate".format(product_head)])

        filed_names.extend(filed_names_2)
        writer = csv.DictWriter(response, filed_names)
        writer.writeheader()

        for idex, obj in enumerate(queryset):
            row_dict = dict()
            row_dict["S.No"] = idex + 1

            other_charges = obj.shipping_charge + obj.cod_charge + obj.other_charge

            other_charges_gst = (round(other_charges / 1.12, 2) * 0.06) * 2

            if obj.total_gst != 0:
                cgst = round((obj.total_gst / 2), 2)
                sgst = cgst
            else:
                cgst = (((obj.pay_amount - other_charges) / 100) * 6)
                sgst = cgst

            cross_amount = (obj.pay_amount - other_charges) - (cgst + sgst)

            row_dict['Invoice Date'] = obj.created_on.strftime("%d-%m-%y")
            row_dict['Invoice Number'] = obj.tracking_client_id
            row_dict['Customer Name'] = obj.name
            row_dict['Customer Email'] = obj.email
            row_dict['Customer Mobile'] = obj.phone

            address = "{door_no}, {street_address}, {city}, {state}, {country}-{postal_code}".format(
                door_no=obj.address.door_no, street_address=obj.address.street_address,
                city=obj.address.city, locality=obj.address.locality,
                state=obj.address.state,
                country=obj.address.country, postal_code=obj.address.postal_code)
            row_dict['Customer Address'] = address
            row_dict['Purchase Order No'] = obj.tracking_client_id
            row_dict['Payment Terms'] = obj.payment_type
            row_dict['Other Charges'] = other_charges - other_charges_gst
            row_dict['Discount'] = obj.coupon_amount
            row_dict['Gross'] = cross_amount
            row_dict['CGST'] = cgst
            row_dict['Other Charges SGST'] = other_charges_gst / 2
            row_dict['Other Charges CGST'] = other_charges_gst / 2
            row_dict['SGST'] = sgst
            row_dict['Net'] = obj.pay_amount

            for index, item in enumerate(obj.order_items.all()):
                row_dict["Product {}".format(index + 1)] = item.product.title
                row_dict["Product {} Qty".format(index + 1)] = item.quantity
                row_dict["Product {} Rate".format(index + 1)] = item.unit_price

            writer.writerow(row_dict)

        return response

    def download_daily_order(self, request):
        if not request.user.is_authenticated:
            return redirect('/')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Orders-{}.csv'.format(
            now().date())
        writer = csv.writer(response)
        writer.writerow(("Order ID", "Date", "Time", "Name", "Email", "Phone Number", "Address Full", "Address Country",
                         "Address State", "Address City", "Payment Mode", "Payment Status", "Currency", "Total Amount",
                         "Final Paid", "Coupon Used", "Coupon Amount", "Wallet Used", "Wallet Amount", "COD Charges",
                         "Shipping Charges", "Product"))

        queryset = self.get_queryset(request).order_by("-created_on")
        filter_dict = {}

        for key, value in request.GET.items():
            if key != "p":
                filter_dict[key] = value

        for obj in queryset.filter(**filter_dict):
            address = "{}, {}\n{}, {}\n{} ({}), \n{}-{}".format(obj.address.door_no, obj.address.street_address,
                                                                obj.address.city, obj.address.state,
                                                                obj.address.locality, obj.address.landmark,
                                                                obj.address.country.title, obj.address.postal_code)

            coupon_used = "Yes" if obj.coupon else "NO"
            coupon_amount = obj.coupon_amount if obj.coupon else 0
            wallet_used = "Yes" if obj.is_wallet else "NO"
            wallet_amount = obj.coupon_amount if obj.is_wallet else 0
            products = ""

            for item in obj.order_items.all():
                products += "{}({}) - {} -{} \n".format(item.product,
                                                        item.product_sku, item.quantity, item.unit_price)

            row_list = [obj.tracking_client_id, obj.created_on.date(), obj.created_on.time(), obj.name, obj.email,
                        "{}-{}".format(obj.dial_code,
                                       obj.phone), address, obj.address.country.title, obj.address.state,
                        obj.address.city, obj.payment_type, obj.payment_status, obj.currency_type, obj.total_amount,
                        obj.pay_amount, coupon_used, coupon_amount, wallet_used, wallet_amount, obj.cod_charge,
                        obj.shipping_charge, products]
            writer.writerow(row_list)
        return response

    @staticmethod
    def download_order_shipping(request):
        if not request.user.is_authenticated:
            return redirect('/')
        return utils.download_shipping()

    @staticmethod
    def update_order_shipping(request):
        if not request.user.is_authenticated:
            return redirect('/')
        Thread(target=order_shipment, args=()).start()

        return redirect("../")

    @staticmethod
    def sync_tracking(request, pk):
        if not request.user.is_authenticated:
            return redirect('/')
        order = int_to_order(pk)
        if order.awb_code and not order.track_url:
            update_tracking_link(order)
        return redirect("../")

    @staticmethod
    def transaction_update(request):
        if not request.user.is_authenticated:
            return redirect('/')
        mismatch_transaction = []
        if request.method == "POST":
            if request.FILES["csv_file"].name.endswith(".csv"):
                csv_file = request.FILES["csv_file"]
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)
                for row in reader:
                    if int(row['captured']) == 1:
                        order = get_object_or_None(
                            models.Orders, tracking_client_id=row['description'])
                        if order and not order.payment_status:
                            mismatch_transaction.append(order)

        return render(request, "transaction_update.html", {"mismatch_transaction": mismatch_transaction})

    @staticmethod
    def download_report(request):
        if not request.user.is_authenticated:
            return redirect('/')

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=Orders-Revenue-{}.csv'.format(
            now().date())

        writer = csv.writer(response)
        writer.writerow(("Date", "Planner (Qty)", "Revenue", "Bundle (Qty)", "Revenue", "Professional Planner (Qty)",
                         "Revenue", "Sticker Book (Qty)", "Revenue", "Total Revenue", "Total Discount",
                         "Total Other Charges"))

        placed_orders = models.Orders.objects.filter(is_success=True, status=1)
        queryset = placed_orders.annotate(day=TruncDate('created_on')).values('day').annotate(c=Count('id')).values(
            'day', 'c')

        for obj in queryset:
            day = obj['day']
            planner = revenue_calculator(models.OrderItems.objects.filter(order__is_success=True, order__status=1,
                                                                          order__created_on__date=day, product=2))

            bundle = revenue_calculator(models.OrderItems.objects.filter(order__is_success=True, order__status=1,
                                                                         order__created_on__date=day, product=1))

            pro_planner = revenue_calculator(models.OrderItems.objects.filter(order__is_success=True, order__status=1,
                                                                              order__created_on__date=day, product=4))

            sticker_book = revenue_calculator(models.OrderItems.objects.filter(order__is_success=True, order__status=1,
                                                                               order__created_on__date=day, product=3))

            pay_amount = placed_orders.filter(created_on__date=day).aggregate(pay_amount=Sum('pay_amount'))[
                'pay_amount']

            cod_charge = placed_orders.filter(created_on__date=day).aggregate(cod_charge=Sum('cod_charge'))[
                'cod_charge']

            coupon_amount = placed_orders.filter(created_on__date=day).aggregate(coupon_amount=Sum('coupon_amount'))[
                'coupon_amount']

            row_list = [day, planner[0], planner[1], bundle[0], bundle[1], pro_planner[0], pro_planner[1],
                        sticker_book[0], sticker_book[1], pay_amount, coupon_amount, cod_charge]

            writer.writerow(row_list)
        return response


def revenue_calculator(qs):
    amount = 0
    qty = qs.aggregate(qty=Sum('quantity'))['qty']
    if qs.first():
        amount = qs.first().unit_price * qty
    return qty, amount
