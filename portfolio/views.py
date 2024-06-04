import pandas as pd
import requests
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .common import calculate_portfolio_value, calculate_weights, comparation_plot
from .forms import TransactionForm, UploadFileForm
from .models import Portfolio, Price, Tick, Transaction
from .services import FileUploadServices


def index(request):
    have_Portfolio = Portfolio.objects.exists()
    context = {}

    if have_Portfolio:
        Portfolios = Portfolio.objects.all()
        available_dates = Price.objects.values_list("date", flat=True).distinct()
        available_dates = [date.strftime("%Y-%m-%d") for date in available_dates]
        min_date = available_dates[0]
        max_date = available_dates[-1]
        context = {
            "Portfolios": Portfolios,
            "available_dates": available_dates,
            "min_date": min_date,
            "max_date": max_date,
        }

    return render(request, "portfolio/index.html", context)


def upload_file(request):
    if request.method == "POST":
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            service = FileUploadServices(file_obj=request.FILES["file"])
            success, error = service.create()
            if success:
                return HttpResponseRedirect(reverse("upload_success"))
            else:
                form.add_error(None, error)  # Add the error to the form
                return render(request, "portfolio/upload.html", {"form": form})
    else:
        form = UploadFileForm()
    return render(request, "portfolio/upload.html", {"form": form})


def upload_success(request):
    return render(request, "portfolio/upload_success.html")


@api_view(["GET"])
def data_In_Range(request):
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
    ticks = Tick.objects.filter(portfolio=portfolio)
    transactions = Transaction.objects.filter(
        portfolio=portfolio, date__range=[fecha_inicio, fecha_fin]
    )

    initial_quantities = {tick.asset: tick.quantity for tick in ticks}
    result = []

    for date in pd.date_range(fecha_inicio, fecha_fin):
        adjusted_quantities = initial_quantities.copy()

        for txn in transactions.filter(date__lte=date):
            if txn.transaction_type == "sell":
                adjusted_quantities[txn.asset] -= txn.quantity
            else:
                adjusted_quantities[txn.asset] += txn.quantity
        temp_ticks = []

        for asset, adjusted_quantity in adjusted_quantities.items():
            tick = Tick(asset=asset, portfolio=portfolio, quantity=adjusted_quantity)
            temp_ticks.append(tick)

        prices = Price.objects.filter(date=date)
        portfolio_value = calculate_portfolio_value(temp_ticks, prices)
        weights = calculate_weights(prices, temp_ticks, portfolio_value)

        result.append(
            {
                "date": date.strftime("%Y-%m-%d"),
                "portfolio": portfolio_id,
                "value": portfolio_value,
                "weights": weights,
            }
        )

    return JsonResponse(result, safe=False)


def compare_data(request):
    fecha_inicio = request.GET.get("fecha_inicio")
    fecha_fin = request.GET.get("fecha_fin")
    portfolio_id = request.GET.get("portfolio")

    if not fecha_inicio or not fecha_fin or not portfolio_id:
        return HttpResponse("Missing parameters", status=400)

    response = requests.get(
        request.build_absolute_uri("/api/portfolio-data/"),
        params={
            "fecha_inicio": fecha_inicio,
            "fecha_fin": fecha_fin,
            "portfolio": portfolio_id,
        },
    )

    if response.status_code != 200:
        return HttpResponse("Error fetching data", status=response.status_code)

    data = response.json()

    value_plot, weights_plot = comparation_plot(data)

    context = {
        "value_plot": value_plot,
        "weights_plot": weights_plot,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "portfolio_id": portfolio_id,
    }
    return render(request, "portfolio/compare_data.html", context)


def reset_transactions(request):
    if request.method == "POST":
        Transaction.objects.all().delete()
        return redirect(reverse("transactions"))


def transaction_list(request):
    transactions = Transaction.objects.all()
    for txn in transactions:
        txn.total_amount = txn.quantity * txn.price

    return render(
        request, "portfolio/transaction_list.html", {"transactions": transactions}
    )


@transaction.atomic
def create_transaction(request):

    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            response = create_transaction_api(request)
            if response.status_code == status.HTTP_201_CREATED:
                return HttpResponseRedirect(reverse("transactions"))
    else:
        form = TransactionForm()
    return render(request, "portfolio/transaction_form.html", {"form": form})


@api_view(["POST"])
def create_transaction_api(request):
    form = TransactionForm(request.data)
    if form.is_valid():
        cleaned_data = form.cleaned_data
        portfolio = cleaned_data["portfolio"]
        date = cleaned_data["date"]
        asset_to_sell = cleaned_data["asset_to_sell"]
        asset_to_buy = cleaned_data["asset_to_buy"]
        value = cleaned_data["value"]
        quantity_to_sell = cleaned_data["quantity_to_sell"]
        quantity_to_buy = cleaned_data["quantity_to_buy"]
        price_to_sell = cleaned_data["price_to_sell"]
        price_to_buy = cleaned_data["price_to_buy"]

        # Create the sell transaction
        Transaction.objects.get_or_create(
            portfolio=portfolio,
            date=date,
            asset=asset_to_sell,
            quantity=quantity_to_sell,
            value=value,
            price=price_to_sell,
            transaction_type="sell",
        )

        # Create the buy transaction
        Transaction.objects.get_or_create(
            portfolio=portfolio,
            date=date,
            asset=asset_to_buy,
            quantity=quantity_to_buy,
            value=value,
            price=price_to_buy,
            transaction_type="buy",
        )

        return Response(
            {"message": "Transaction created successfully"},
            status=status.HTTP_201_CREATED,
        )
    return Response({"errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)
