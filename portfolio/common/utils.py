from decimal import Decimal


def calculate_actives_cuantity(weight, price, portafolio):
    value = portafolio.value
    quantity = (Decimal(weight) * value) / price.value

    return quantity


def calculate_weights(prices, quantites, portf_value):
    weights = {}
    for quantity in quantites:
        precio = prices.get(asset=quantity.asset).value
        weight = (precio * quantity.quantity) / portf_value
        weights[quantity.asset.name] = weight
    return weights


def calculate_portfolio_value(quantities, prices):
    value = 0
    for quantity in quantities:
        price = prices.get(asset=quantity.asset).value
        value += price * quantity.quantity
    value = round(value, 2)
    return value
