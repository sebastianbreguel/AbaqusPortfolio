def calculate_actives_cuantity(asset, weight, prices, portafolio):
    value = portafolio.value
    weight = weight.weight
    price = prices[asset.name]
    quantity = (weight * value) / price

    return quantity
