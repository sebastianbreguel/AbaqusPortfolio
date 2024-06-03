from django import forms

from .models import Asset, Portfolio, Price, Transaction


class UploadFileForm(forms.Form):
    file = forms.FileField()


class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ["date", "value", "portfolio"]

    portfolio = forms.ModelChoiceField(
        queryset=Portfolio.objects.all(), empty_label="Seleccione un portafolio"
    )
    asset_to_sell = forms.ModelChoiceField(
        queryset=Asset.objects.all(), empty_label="Seleccione un activo a vender"
    )
    asset_to_buy = forms.ModelChoiceField(
        queryset=Asset.objects.all(), empty_label="Seleccione un activo a comprar"
    )
    date = forms.DateField(widget=forms.DateInput(attrs={"type": "date"}))
    value = forms.IntegerField(min_value=0, required=False, label="Cantidad")

    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get("date")
        asset_to_sell = cleaned_data.get("asset_to_sell")
        asset_to_buy = cleaned_data.get("asset_to_buy")
        value = cleaned_data.get("value")

        if date and asset_to_sell:
            try:
                price_to_sell = Price.objects.get(asset=asset_to_sell, date=date)
                cleaned_data["quantity_to_sell"] = self.calculate_quantity(
                    value, price_to_sell.value
                )
                cleaned_data["price_to_sell"] = price_to_sell.value
            except Price.DoesNotExist:
                self.add_error(
                    "asset_to_sell",
                    "No hay precio disponible para el activo seleccionado en la fecha proporcionada.",
                )

        if date and asset_to_buy:
            try:
                price_to_buy = Price.objects.get(asset=asset_to_buy, date=date)
                cleaned_data["quantity_to_buy"] = self.calculate_quantity(
                    value, price_to_buy.value
                )
                cleaned_data["price_to_buy"] = price_to_buy.value
            except Price.DoesNotExist:
                self.add_error(
                    "asset_to_buy",
                    "No hay precio disponible para el activo seleccionado en la fecha proporcionada.",
                )

        return cleaned_data

    def calculate_quantity(self, value, price):
        return value / price if price != 0 else 0
