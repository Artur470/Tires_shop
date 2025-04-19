from django.contrib import admin
from .models import Product,   Condition, TireType, Season, BodyType


class ProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'price', 'promotion', 'quantity', 'promotion_category']
    search_fields = ['title', 'category__label']
    list_filter = ['category', 'promotion_category']


    filter_horizontal = ('promotion_category',)

admin.site.register(Product)





admin.site.register(Condition)
admin.site.register(TireType)
admin.site.register(Season)
admin.site.register(BodyType)
