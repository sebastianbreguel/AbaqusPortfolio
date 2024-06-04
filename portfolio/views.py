import requests
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from .common import comparation_plot
from .forms import TransactionForm, UploadFileForm
from .models import Portfolio, Price, Transaction
from .services import FileUploadServices, create_transaction_api, get_data_in_range


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
def data_in_range(request):
    fecha_inicio = request.query_params.get("fecha_inicio")
    fecha_fin = request.query_params.get("fecha_fin")
    portfolio_id = request.query_params.get("portfolio")

    if not fecha_inicio or not fecha_fin or not portfolio_id:
        return Response(
            {"error": "Missing parameters"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        result = get_data_in_range(fecha_inicio, fecha_fin, portfolio_id)
    except Portfolio.DoesNotExist:
        return Response(
            {"error": "Portfolio not found"}, status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

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


def create_transaction(request):
    min_date = (
        Price.objects.values_list("date", flat=True)
        .order_by("date")
        .first()
        .strftime("%Y-%m-%d")
    )
    max_date = (
        Price.objects.values_list("date", flat=True)
        .order_by("-date")
        .first()
        .strftime("%Y-%m-%d")
    )

    if request.method == "POST":
        form = TransactionForm(request.POST)
        if form.is_valid():
            response = create_transaction_api(request)
            if response.status_code == status.HTTP_201_CREATED:
                return HttpResponseRedirect(reverse("transactions"))
    else:
        form = TransactionForm()

    form.fields["date"].widget.attrs.update(
        {
            "min": min_date,
            "max": max_date,
            "value": min_date,  # Establecer el valor predeterminado como la fecha mínima
        }
    )

    return render(
        request,
        "portfolio/transaction_form.html",
        {"form": form, "min_date": min_date, "max_date": max_date},
    )
