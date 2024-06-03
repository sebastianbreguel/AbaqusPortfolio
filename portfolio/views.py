import os
import tempfile
from datetime import datetime
import io
import matplotlib

matplotlib.use('Agg')  # Usar el backend 'Agg' para evitar problemas de GUI
import matplotlib.pyplot as plt
import pandas as pd
from django.http import HttpResponse
from rest_framework.decorators import api_view

from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .forms import UploadFileForm
from .models import Asset, Holding, Portfolio, Price
from .utils import (
    calculate_actives_cuantity,
    calculate_portfolio_value,
    calculate_weights,
)

# Create your views here.


def handle_uploaded_file(f):

    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, "uploaded_file.xlsx")
    with open(file_path, "wb+") as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    try:
        df_weights = pd.read_excel(file_path, sheet_name="weights")
        df_prices = pd.read_excel(file_path, sheet_name="Precios")
        df_prices.reset_index(drop=False, inplace=True)
        df_prices.rename(columns={"index": "date_id"}, inplace=True)

    except Exception as e:
        print(f"Error reading the Excel file: {e}")
        return None, None

    portfolio_columns = [col for col in df_weights.columns if "portafolio" in col]
    portfolio_columns = {col: col.split(" ")[1] for col in portfolio_columns}
    initial_date = datetime.strptime("2022-02-15", "%Y-%m-%d").date()

    df_weights = df_weights.melt(
        id_vars=["Fecha", "activos"],
        value_vars=[f"{portfolio}" for portfolio in portfolio_columns.keys()],
        var_name="portafolio",
        value_name="weight",
    )

    df_weights["portafolio"] = df_weights["portafolio"].apply(
        lambda x: portfolio_columns[x]
    )

    # Activos
    assets = df_prices.columns[2:]
    for asset_name in assets:
        Asset.objects.get_or_create(name=asset_name)

    # Portafolios
    for portafolio in df_weights["portafolio"].unique():
        Portfolio.objects.get_or_create(name=f"Portfolio {portafolio}")

    # Precios
    for _, row in df_prices.iterrows():
        date = row["Dates"]
        date = date.strftime("%Y-%m-%d")
        date_id = row["date_id"]
        for asset_name in assets:
            asset = Asset.objects.get(name=asset_name)
            price = row[asset_name]
            Price.objects.get_or_create(
                asset=asset, date=date, value=price, date_id=date_id
            )

    # Holdings
    for _, row in df_weights.iterrows():
        date = row["Fecha"]
        date = date.strftime("%Y-%m-%d")
        asset = Asset.objects.get(name=row["activos"])
        price = Price.objects.get(asset=asset, date=initial_date)
        portfolio = Portfolio.objects.get(name=f'Portfolio {row["portafolio"]}')
        weight = float(row["weight"])

        quantity = calculate_actives_cuantity(weight, price, portfolio)
        Holding.objects.create(
            asset=asset,
            portfolio=portfolio,
            date=initial_date,
            quantity=quantity,
            weight=weight,
        )


def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            handle_uploaded_file(request.FILES["file"])
            return HttpResponseRedirect(reverse("upload_success"))
    else:
        form = UploadFileForm()
    return render(request, "portfolio/upload.html", {"form": form})


def upload_success(request):
    return render(request, "portfolio/upload_success.html")



@api_view(['GET'])
def data_In_Range( request):
    """
    request:
    - fecha_inicio: value of the date that we want to calculate the weights
    - fecha_fin: value of the date that we want to calculate the weights
    - portfolio: number of portafolio
    """
    fecha_inicio = request.query_params.get("fecha_inicio")
    fecha_fin = request.query_params.get("fecha_fin")
    portfolio_id = int(request.query_params.get("portfolio"))

    if not fecha_inicio or not fecha_fin or not portfolio_id:
        return Response(
            {"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST
        )
    portfolio = Portfolio.objects.get(name=f"Portfolio {portfolio_id}")
    Quantities = Holding.objects.filter(portfolio=portfolio)

    prices = Price.objects.filter(date=fecha_inicio)
    prices_range = Price.objects.filter(date__range=[fecha_inicio, fecha_fin])

    for price in prices_range:
        date_id = price.date_id
        portf_value = calculate_portfolio_value(Quantities, prices)
        weights = calculate_weights(prices, Quantities, portf_value)

    result = []
    for date in pd.date_range(fecha_inicio, fecha_fin):
        prices = Price.objects.filter(date=date)
        date_id = prices[0].date_id
        portf_value = calculate_portfolio_value(Quantities, prices)
        weights = calculate_weights(prices, Quantities, portf_value)
        result.append(
            {
                "date_id": date_id,
                "portfolio": portfolio_id,
                "value": portf_value,
                "weights": weights,
            }
        )
    # Convertir los datos a DataFrame

    return JsonResponse(result, safe=False)
