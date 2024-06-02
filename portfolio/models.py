from django.db import models

class Asset(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Portfolio(models.Model):
    name = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=20, decimal_places=2, default=1000000000)

    def __str__(self):
        return self.name

class Price(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    date = models.DateField()
    price = models.DecimalField(max_digits=20, decimal_places=2)
    date_id = models.IntegerField(blank=True, null=True)


    def __str__(self):
        return f"{self.asset.name} - {self.date} - ${self.price}"

class Weight(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    date = models.DateField()
    weight = models.DecimalField(max_digits=5, decimal_places=4)

    def __str__(self):
        return f"{self.portfolio.name}: - {self.asset.name}  - {self.weight} - {self.date}"

class Quantity(models.Model):
    asset = models.ForeignKey(Asset, on_delete=models.CASCADE)
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=20, decimal_places=4)
    date = models.DateField()

    def __str__(self):
        return f"{self.portfolio.name} - {self.asset.name} - {self.quantity} - {self.date}"
