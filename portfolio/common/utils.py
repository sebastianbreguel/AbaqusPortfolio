from decimal import Decimal

import pandas as pd
import plotly.express as px

from portfolio.models import Price


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


def comparation_plot(data):

    dates = [entry["date"] for entry in data]
    values = [entry["value"] for entry in data]
    weights = [entry["weights"] for entry in data]

    # Data preparation for weights plot
    weights_df = pd.DataFrame(weights, index=dates)
    weights_df = weights_df.apply(pd.to_numeric, errors="coerce").fillna(0)

    # Plot portfolio values using Plotly
    value_fig = px.line(x=dates, y=values, labels={"x": "Date", "y": "Value"})
    value_fig.update_layout(
        yaxis=dict(autorange=True, title="Valor", type="linear"),
        xaxis=dict(title="Fecha"),
    )
    value_plot = value_fig.to_html(full_html=False)

    # Plot weights as stacked area chart using Plotly
    weights_df = weights_df.reset_index().melt(
        id_vars=["index"], var_name="Asset", value_name="Weight"
    )
    weights_fig = px.area(weights_df, x="index", y="Weight", color="Asset")
    weights_fig.update_layout(
        xaxis=dict(type="category", categoryorder="category ascending")
    )
    weights_fig.update_layout(
        yaxis=dict(autorange=True, title="Weight", type="linear"),
        xaxis=dict(title="Fecha"),
    )
    weights_plot = weights_fig.to_html(full_html=False)

    return value_plot, weights_plot


def get_minmax_range():
    min_date_obj = Price.objects.values_list("date", flat=True).order_by("date").first()
    max_date_obj = (
        Price.objects.values_list("date", flat=True).order_by("-date").first()
    )

    if not min_date_obj or not max_date_obj:
        return None, None

    min_date = min_date_obj.strftime("%Y-%m-%d")
    max_date = max_date_obj.strftime("%Y-%m-%d")
    return min_date, max_date
