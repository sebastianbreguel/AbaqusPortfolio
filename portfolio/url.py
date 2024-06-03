from django.urls import path

from .views import (
    compare_data,
    create_transaction,
    create_transaction_api,
    data_In_Range,
    index,
    reset_transactions,
    transaction_list,
    upload_file,
    upload_success,
)

urlpatterns = [
    path("", index, name="index"),
    path("upload/", upload_file, name="upload_file"),
    path("upload/success/", upload_success, name="upload_success"),
    path("compare_data/", compare_data, name="compare_data"),
    path("api/portfolio-data/", data_In_Range, name="portfolio_data"),
    path("transactions/", transaction_list, name="transactions"),
    path("transactions/new/", create_transaction, name="create_transaction"),
    path("transactions/reset/", reset_transactions, name="reset_transactions"),
    path("api/transactions/", create_transaction_api, name="create_transaction_api"),
]
