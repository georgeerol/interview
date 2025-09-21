from django.contrib import admin

from .domain import Business


@admin.register(Business)
class BusinessAdmin(admin.ModelAdmin):
	list_display = ("name", "city", "state", "latitude", "longitude")
	search_fields = ("name", "city", "state")


