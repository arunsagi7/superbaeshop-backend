import datetime

from rest_framework import viewsets, permissions, mixins, exceptions, response, status, generics
from rest_framework.decorators import action

from authentication.utils import SendEmailViewMixin
from . import models, serializers, utils


class CartViewSet(mixins.RetrieveModelMixin, mixins.DestroyModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    use this endpoint to do following operations
        1. Add to cart
        2. Edit Cart Quantity
        3. Remove Cart item
        4. List My Cart Item
    """

    permission_classes = (
        permissions.IsAuthenticated,
    )

    model = models.Cart
    serializer_class = serializers.CartSerializers

    def get_queryset(self):
        if not hasattr(self.request.user, "userprofile"):
            raise exceptions.NotAcceptable()
        return self.request.user.userprofile.my_cart.all().order_by("created_on").distinct()
    def get_object(self):
        product_id = self.kwargs.get('pk')
        try:
            return self.get_queryset().get(product_id=product_id)
        except models.Cart.DoesNotExist:
            raise exceptions.NotFound("Cart item not found")

    def create(self, request):
        serializer = self.get_serializer(data=request.data, many=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
        else:
            raise exceptions.ValidationError(serializer.errors)
        my_cart = self.request.user.userprofile.my_cart.all()
        serializer = self.get_serializer(my_cart, many=True, context={"request": request})

        return response.Response(serializer.data)

    @action(detail=False, methods=['GET'])
    def list_cart(self, request):
        data = dict()
        my_cart = self.get_queryset()
        serializer = self.get_serializer(my_cart, many=True, context={"request": request})
        data['cart'] = serializer.data

        data['offer'] = utils.offer_calculation(my_cart)
        if data['offer']:
            data['is_coupon'] = False
            data['is_wallet'] = False
        else:
            data['is_coupon'] = True
            data['is_wallet'] = True
        return response.Response(data)

    @action(detail=False, methods=['GET'], url_path='item/(?P<product_id>[^/.]+)')
    def get_item(self, request, product_id=None):
        """Retrieve a cart item by product ID, showing image and price."""
        try:
            cart_item = self.get_queryset().get(product_id=product_id)
        except models.Cart.DoesNotExist:
            raise exceptions.NotFound("Cart item not found")
        serializer = self.get_serializer(cart_item, context={"request": request})
        return response.Response(serializer.data)

    @action(detail=False, methods=['DELETE'], url_path='item/(?P<product_id>[^/.]+)')
    def delete_item(self, request, product_id=None):
        """Delete a cart item by product ID."""
        try:
            cart_item = self.get_queryset().get(product_id=product_id)
        except models.Cart.DoesNotExist:
            raise exceptions.NotFound("Cart item not found")
        cart_item.delete()
        
        data = dict()
        my_cart = request.user.userprofile.my_cart.all().order_by("created_on").distinct()
        serializer = self.get_serializer(my_cart, many=True, context={"request": request})
        data['cart'] = serializer.data

        data['offer'] = utils.offer_calculation(my_cart)
        if data['offer']:
            data['is_coupon'] = False
            data['is_wallet'] = False
        else:
            data['is_coupon'] = True
            data['is_wallet'] = True
        return response.Response(data)

    @action(detail=False, methods=['POST'])
    def update_create(self, request):
        data = dict()
        serializer = self.get_serializer(data=request.data, many=True, context={"request": request})
        if serializer.is_valid():
            serializer.save()
        else:
            raise exceptions.ValidationError(serializer.errors)

        my_cart = request.user.userprofile.my_cart.all()
        serializer = self.get_serializer(my_cart, many=True, context={"request": request})
        data['cart'] = serializer.data

        data['offer'] = utils.offer_calculation(my_cart)
        if data['offer']:
            data['is_coupon'] = False
            data['is_wallet'] = False
        else:
            data['is_coupon'] = True
            data['is_wallet'] = True

        return response.Response(data)

    @action(detail=False, methods=['POST'])
    def merge_guest_cart(self, request):
        """
        Merge guest cart items (by X-Guest-Session-ID) into the authenticated user's cart.
        Called right after login/signup OTP verification so guest items are not lost.
        """
        if not hasattr(request.user, "userprofile"):
            raise exceptions.NotAcceptable()

        session_id = (
            request.headers.get("X-Guest-Session-ID")
            or request.data.get("session_id")
        )
        if not session_id:
            # No guest session — just return the user's existing cart
            return self.list_cart(request)

        guest_items = models.GuestCart.objects.filter(session_id=session_id)
        user_profile = request.user.userprofile

        for guest_item in guest_items:
            existing = models.Cart.objects.filter(
                user=user_profile, product=guest_item.product
            ).first()
            if existing:
                # Keep the higher quantity (capped at 9)
                existing.quantity = min(max(existing.quantity, guest_item.quantity), 9)
                if guest_item.color_code and not existing.color_code:
                    existing.color_code = guest_item.color_code
                if guest_item.is_offer:
                    existing.is_offer = True
                existing.save()
            else:
                models.Cart.objects.create(
                    user=user_profile,
                    product=guest_item.product,
                    quantity=min(guest_item.quantity, 9),
                    is_offer=guest_item.is_offer,
                    color_code=guest_item.color_code,
                )

        # Clear guest cart after successful merge
        guest_items.delete()

        return self.list_cart(request)

    @action(detail=False, methods=['DELETE'])
    def clear_cart(self, request):
        request.user.userprofile.my_cart.all().delete()
        return response.Response(status=status.HTTP_204_NO_CONTENT)


    @action(detail=True, methods=['DELETE'])
    def remove_item(self, request, pk=None):
        try:
            cart_item = self.get_queryset().get(pk=pk)
            cart_item.delete()
            return response.Response(status=status.HTTP_204_NO_CONTENT)
        except models.Cart.DoesNotExist:
            raise exceptions.NotFound("Cart item not found")


class CartRemainderEmailView(generics.GenericAPIView, SendEmailViewMixin):
    """
    use this endpoint to do following operations
    1. Daily basic send cart remainder email to yesterday cart added p
    """

    def get(self, request):
        today = datetime.datetime.today()
        three_days_before = datetime.datetime.today() - datetime.timedelta(days=3)
        profiles = models.UserProfile.objects.filter(my_cart__isnull=False,
                                                     my_cart__created_on__range=[three_days_before, today]).order_by(
            "-my_cart__created_on").distinct()
        for idx, profile in enumerate(profiles):
            if not profile.my_orders.filter(is_success=True, created_on__month=today.month,
                                            created_on__year=today.year):
                self.subject_template_name = 'cart-remainder_subject.txt'
                self.html_body_template_name = 'cart-remainder_notify.html'

                sms_context = {"profile": profile}
                self.send_email(profile.user.email, sms_context)

        return response.Response({"data": "Email Sent {}".format(profiles.count())})


class GuestCartViewSet(viewsets.GenericViewSet):
    permission_classes = [permissions.AllowAny]
    serializer_class = serializers.GuestCartSerializers
    queryset = models.GuestCart.objects.all()

    def get_session_id(self, request):
        session_id = request.headers.get("X-Guest-Session-ID") or request.data.get("session_id")
        if not session_id:
            raise exceptions.NotAcceptable("X-Guest-Session-ID header or session_id parameter is required")
        return session_id

    @action(detail=False, methods=['GET'])
    def list_cart(self, request):
        session_id = self.get_session_id(request)
        my_cart = self.get_queryset().filter(session_id=session_id).order_by("created_on").distinct()
        data = dict()
        serializer = self.get_serializer(my_cart, many=True, context={"request": request})
        data['cart'] = serializer.data
        data['offer'] = utils.offer_calculation(my_cart)
        if data['offer']:
            data['is_coupon'] = False
            data['is_wallet'] = False
        else:
            data['is_coupon'] = True
            data['is_wallet'] = True
        return response.Response(data)

    @action(detail=False, methods=['POST'])
    def update_create(self, request):
        session_id = self.get_session_id(request)
        # Deep copy to avoid mutating immutable DRF request.data
        import copy
        request_data = copy.deepcopy(request.data)
        if isinstance(request_data, list):
            for item in request_data:
                item['session_id'] = session_id
        elif isinstance(request_data, dict):
            request_data['session_id'] = session_id

        serializer = self.get_serializer(data=request_data, many=isinstance(request_data, list), context={"request": request})
        if serializer.is_valid():
            serializer.save()
            my_cart = self.get_queryset().filter(session_id=session_id).order_by("created_on").distinct()
            data = dict()
            res_serializer = self.get_serializer(my_cart, many=True, context={"request": request})
            data['cart'] = res_serializer.data
            data['offer'] = utils.offer_calculation(my_cart)
            if data['offer']:
                data['is_coupon'] = False
                data['is_wallet'] = False
            else:
                data['is_coupon'] = True
                data['is_wallet'] = True
            return response.Response(data)
        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['DELETE'], url_path='item/(?P<product_id>[^/.]+)')
    def delete_item(self, request, product_id=None):
        session_id = self.get_session_id(request)
        try:
            cart_item = self.get_queryset().get(session_id=session_id, product_id=product_id)
        except models.GuestCart.DoesNotExist:
            raise exceptions.NotFound("Cart item not found")
        cart_item.delete()
        
        my_cart = self.get_queryset().filter(session_id=session_id).order_by("created_on").distinct()
        data = dict()
        serializer = self.get_serializer(my_cart, many=True, context={"request": request})
        data['cart'] = serializer.data

        data['offer'] = utils.offer_calculation(my_cart)
        if data['offer']:
            data['is_coupon'] = False
            data['is_wallet'] = False
        else:
            data['is_coupon'] = True
            data['is_wallet'] = True
        return response.Response(data)
