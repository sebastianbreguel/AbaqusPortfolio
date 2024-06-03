from django.contrib import admin

from .models import Asset, Holding, Portfolio, Price, Weight

admin.site.register(Asset)
admin.site.register(Price)
admin.site.register(Holding)
admin.site.register(Portfolio)
admin.site.register(Weight)
