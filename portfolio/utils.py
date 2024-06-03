from decimal import Decimal


def calculate_actives_cuantity(weight, price, portafolio):
    value = portafolio.value
    quantity = (Decimal(weight) * value) / price.value

    return quantity


def calculate_weights(prices, ticks, portf_value):
    weights = {}
    for tick in ticks:
        precio = prices.get(asset=tick.asset)
        quantity = tick.quantity
        weight = (precio.value * quantity) / portf_value
        weights[precio.asset.name] = weight
    return weights


def calculate_portfolio_value(ticks, prices, have_transaction=False):
    value = 0
    for tick in ticks:
        price = prices.get(asset=tick.asset).value
        value += price * tick.quantity
    value = round(value, 2)
    return value
