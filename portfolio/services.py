import os
import tempfile
from datetime import datetime
from decimal import Decimal

import pandas as pd
from django.db import transaction

from .models import Asset, Portfolio, Price, Tick
from .utils import calculate_actives_cuantity


class FileUploadServices:

    def __init__(self, file_obj):
        self.file_obj = file_obj
        self.temp_dir = tempfile.gettempdir()
        self.file_path = os.path.join(self.temp_dir, "uploaded_file.xlsx")

    def _save_temp_file(self):
        with open(self.file_path, "wb+") as destination:
            for chunk in self.file_obj.chunks():
                destination.write(chunk)

    def _read_excel_file(self):
        try:
            df_weights = pd.read_excel(self.file_path, sheet_name="weights")
            df_prices = pd.read_excel(self.file_path, sheet_name="Precios")
            df_prices.reset_index(drop=False, inplace=True)
            df_prices.rename(columns={"index": "date_id"}, inplace=True)
        except Exception as e:
            print(f"Error reading the Excel file: {e}")
            return None, None, str(f"Error reading the Excel file: {e}")

        return df_weights, df_prices, None

    def _prepare_data(self, df_weights, df_prices):
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
        return df_weights, df_prices, initial_date

    @transaction.atomic
    def create(self):
        self._save_temp_file()
        df_weights, df_prices, error = self._read_excel_file()
        if error:
            return False, error
        df_weights, df_prices, initial_date = self._prepare_data(df_weights, df_prices)
        try:
            # Activos
            assets = df_prices.columns[2:]
            for asset_name in assets:
                create_or_update_asset(asset_name)

            # Portafolios
            for portafolio in df_weights["portafolio"].unique():
                create_or_update_portfolio(f"Portfolio {portafolio}")

            # Precios
            for _, row in df_prices.iterrows():
                date = row["Dates"].strftime("%Y-%m-%d")
                date_id = row["date_id"]
                for asset_name in assets:
                    price = row[asset_name]
                    create_or_update_price(asset_name, date, date_id, price)

            # Ticks
            for _, row in df_weights.iterrows():
                date = row["Fecha"].strftime("%Y-%m-%d")
                asset_name = row["activos"]
                portfolio_name = f"Portfolio {row['portafolio']}"
                weight = float(row["weight"])
                price = Price.objects.get(asset__name=asset_name, date=initial_date)
                portafolio = Portfolio.objects.get(name=portfolio_name)
                quantity = calculate_actives_cuantity(weight, price, portafolio)
                create_or_update_tick(
                    asset_name, portfolio_name, date, quantity, weight
                )

        except Exception as e:
            return False, f"Error creating the data: {e}"

        return True, None


def update_instance_fields(instance, data):
    """
    Update the instance with the given data only if the data has changed.
    """
    update_fields = []
    for field, value in data.items():
        if value is None:
            continue

        current_value = getattr(instance, field)

        if isinstance(current_value, Decimal):
            new_value = Decimal(value).quantize(Decimal("0.01"))
        else:
            new_value = value

        if current_value != new_value:
            setattr(instance, field, new_value)
            update_fields.append(field)
    if update_fields:
        instance.full_clean()
        instance.save(update_fields=update_fields)
    return instance


@transaction.atomic
def create_or_update_asset(asset_name):
    asset, created = Asset.objects.get_or_create(name=asset_name)
    if not created:
        asset = update_instance_fields(asset, {"name": asset_name})
    return asset


@transaction.atomic
def create_or_update_portfolio(portfolio_name, value=None):
    portfolio, created = Portfolio.objects.get_or_create(name=portfolio_name)
    if not created:
        portfolio = update_instance_fields(portfolio, {"value": value})
    return portfolio


@transaction.atomic
def create_or_update_price(asset_name, date, date_id, value=None):
    asset = Asset.objects.get(name=asset_name)
    price, created = Price.objects.get_or_create(
        asset=asset, date=date, defaults={"value": value, "date_id": date_id}
    )
    if not created:
        price = update_instance_fields(price, {"value": value, "date_id": date_id})
    return price


@transaction.atomic
def create_or_update_tick(asset_name, portfolio_name, date, quantity, weight):
    asset = Asset.objects.get(name=asset_name)
    portfolio = Portfolio.objects.get(name=portfolio_name)
    tick, created = Tick.objects.get_or_create(
        asset=asset,
        portfolio=portfolio,
        date=date,
        defaults={"quantity": quantity, "weight": weight},
    )
    if not created:
        tick = update_instance_fields(tick, {"quantity": quantity, "weight": weight})
    return tick
