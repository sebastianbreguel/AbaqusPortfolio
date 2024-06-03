from django.contrib import admin

from .models import Asset, Portfolio, Price, Tick, Transaction

admin.site.register(Asset)
admin.site.register(Portfolio)
admin.site.register(Price)
admin.site.register(Tick)
admin.site.register(Transaction)
