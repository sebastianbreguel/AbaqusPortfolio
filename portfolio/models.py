from django.core.exceptions import ValidationError
from django.db import models


class Asset(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Portfolio(models.Model):
    name = models.CharField(max_length=100, unique=True)
    value = models.DecimalField(max_digits=25, decimal_places=2, default=1000000000)

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        if self.value < 0:
            raise ValidationError("Value must be greater than 0")


class Price(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    date_id = models.IntegerField(blank=True, null=True)
    value = models.DecimalField(max_digits=20, decimal_places=2)

    class Meta:
        unique_together = ("asset", "date")

    def __str__(self):
        return f"{self.asset.name} - {self.date} - ${self.value}"

    def clean(self):
        if self.value < 0:
            raise ValidationError("Price must be greater than 0")


class Holding(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    date = models.DateField()
    weight = models.DecimalField(max_digits=7, decimal_places=6, default=0)

    class Meta:
        unique_together = ("asset", "date", "portfolio")

    def __str__(self):
        return (
            f"{self.portfolio.name} - {self.asset.name} - {self.quantity} - {self.date}"
        )

    def clean(self):
        if self.quantity < 0:
            raise ValidationError("Quantity must be greater than 0")
