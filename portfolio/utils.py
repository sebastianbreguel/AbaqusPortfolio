def calculate_actives_cuantity(asset, weight, prices, portafolio):
    value = portafolio.value
    weight = weight.weight
    price = prices[asset.name]
    quantity = (weight * value) / price

    return quantity


def calculate_weights(prices, quantites, portf_value):
    weights = {}
    for quantity in quantites:
        precio = prices.get(asset=quantity.asset).price
        weight = (precio * quantity.quantity) / portf_value
        weights[quantity.asset.name] = weight
    return weights


def calculate_portfolio_value(quantities, prices):
    value = 0
    for quantity in quantities:
        price = prices.get(asset=quantity.asset).price
        value += price * quantity.quantity
    return value
