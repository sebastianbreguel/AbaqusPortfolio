from django import forms

from .models import Asset, Portfolio, Price, Transaction, Tick


class UploadFileForm(forms.Form):
    file = forms.FileField(label='Selecciona un archivo')

    def clean_file(self):
        file = self.cleaned_data.get('file')
        if not file.name.endswith('.xlsx'):
            raise forms.ValidationError('El archivo debe tener una extensión .xlsx')
        return file

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
        portfolio = cleaned_data.get("portfolio")
        asset_to_sell = cleaned_data.get("asset_to_sell")
        asset_to_buy = cleaned_data.get("asset_to_buy")
        value = cleaned_data.get("value")

        if asset_to_buy == asset_to_sell:
            self.add_error(
                "asset_to_buy",
                "El activo a comprar no puede ser el mismo que el activo a vender.",
            )


        if portfolio and asset_to_sell and value:
            try:
                tick = Tick.objects.get(portfolio=portfolio, asset=asset_to_sell)
                price = Price.objects.get(asset=asset_to_sell, date=date)
                tick_value = tick.quantity * price.value
                if value > tick_value:
                    self.add_error('value', f"No puedes vender más de {round(tick_value,2)} del activo seleccionado.")

            except Tick.DoesNotExist:
                self.add_error('asset_to_sell', "El activo seleccionado no está disponible en el portafolio.")

            
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
