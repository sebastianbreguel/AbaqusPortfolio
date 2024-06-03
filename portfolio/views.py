import os
import tempfile
from datetime import datetime

import pandas as pd
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render
from django.urls import reverse

from .forms import UploadFileForm
from .models import Asset, Holding, Portfolio, Price, Weight
from .utils import calculate_actives_cuantity

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

    # Obtener las columnas de los portafolios
    portfolio_columns = [col for col in df_weights.columns if "portafolio" in col]
    portfolio_columns = {col: col.split(" ")[1] for col in portfolio_columns}

    df_weights = df_weights.melt(
        id_vars=["Fecha", "activos"],
        value_vars=[f"{portfolio}" for portfolio in portfolio_columns.keys()],
        var_name="portafolio",
        value_name="weight",
    )

    # Renombrar todas las filas para cada portafolio
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
                asset=asset, date=date, price=price, date_id=date_id
            )

    # Weights
    for _, row in df_weights.iterrows():
        date = row["Fecha"]
        date = date.strftime("%Y-%m-%d")
        asset = Asset.objects.get(name=row["activos"])
        portfolio = Portfolio.objects.get(name=f'Portfolio {row["portafolio"]}')
        weight = row["weight"]
        Weight.objects.get_or_create(
            asset=asset,
            portfolio=portfolio,
            date=date,
            weight=weight,
        )

    # Holdings for the initial date
    initial_date = datetime.strptime("2022-02-15", "%Y-%m-%d").date()
    initial_prices = {
        price.asset.name: price.price
        for price in Price.objects.filter(date=initial_date)
    }
    portfolios = Portfolio.objects.all()
    for portfolio in portfolios:
        weights = Weight.objects.filter(portfolio=portfolio, date=initial_date)
        for weight in weights:
            print("assets", weight.asset)
            print(portfolio)
            print(date)
            quantity = calculate_actives_cuantity(
                weight.asset, weight, initial_prices, portfolio
            )
            asset = Asset.objects.get(name=weight.asset.name)
            Holding.objects.create(
                asset=asset, portfolio=portfolio, date=initial_date, quantity=quantity
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
