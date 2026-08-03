from itertools import chain

from django.db.models import Sum

from offers_management.serializers import OfferSerializers


def offer_calculation(user_cart):
    cart_offer = [item.product.category.categories_offers.all() for item in user_cart]
    offers_cart = set(list(chain.from_iterable(cart_offer)))

    for offer in offers_cart:
        if offer.type == 2:
            offer_amount = 0
            cart_id = []
            buy_count = offer.min_product
            offer_count = offer.offer_value
            offer_product = user_cart.filter(product__category__categories_offers__in=[offer])
            cart_count = offer_product.aggregate(count=Sum('quantity'))['count']

            if buy_count <= cart_count:
                if cart_count >= (buy_count + offer_count):
                    discount_count = offer_count
                else:
                    discount_count = cart_count - buy_count

                if discount_count > 0:

                    cart_products = offer_product.order_by("product__product_country__selling_price", "id")[
                                    :discount_count]
                    remaining_product = discount_count
                    for cart_item in cart_products:
                        if remaining_product == 0:
                            break
                        if cart_item.quantity > remaining_product:
                            count_item = remaining_product
                        else:
                            count_item = cart_item.quantity

                        discount = cart_item.product.product_country.get(country=1).selling_price * count_item
                        offer_amount += discount
                        offer_obj = OfferSerializers(offer).data
                        cart_id.append(
                            {"id": cart_item.id, "qty": count_item, "discount": discount, "offer": offer_obj})
                        remaining_product = remaining_product - count_item
                    return {"offer_amount": offer_amount, "cart_id": cart_id}

    return None
