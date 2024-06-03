from django.core.exceptions import ValidationError
from django.db import models


class Asset(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.DecimalField(max_digits=35, decimal_places=10, default=1000000000)

    def __str__(self):
        return f"Portafolio {self.id}"

    def clean(self):
        if self.value < 0:
            raise ValidationError("Value must be greater than 0")


class Price(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    date_id = models.IntegerField(blank=True, null=True)
    value = models.DecimalField(max_digits=30, decimal_places=10)

    class Meta:
        unique_together = ("asset", "date")

    def __str__(self):
        return f"{self.asset.name} - {self.date} - ${self.value}"

    def clean(self):
        if self.value < 0:
            raise ValidationError("Price must be greater than 0")


class Tick(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=25, decimal_places=10)
    date = models.DateField()
    weight = models.DecimalField(max_digits=10, decimal_places=9, default=0)

    class Meta:
        unique_together = ("asset", "date", "portfolio")

    def __str__(self):
        return (
            f"{self.portfolio.name} - {self.asset.name} - {self.quantity} - {self.date}"
        )

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity must be greater than 0")


class Transaction(models.Model):
    TRANSACTION_TYPES = [
        ("buy", "Compra"),
        ("sell", "Venta"),
    ]

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=2)
    date = models.DateField()
    quantity = models.DecimalField(max_digits=20, decimal_places=4, default=0)
    transaction_type = models.CharField(max_length=4, choices=TRANSACTION_TYPES)
    value = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.get_transaction_type_display()} de {self.asset.name}: {self.quantity} a un precio ${self.price} en {self.portfolio.name} el {self.date}"
