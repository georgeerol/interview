from django.db import models
from .constants import US_STATES


class Business(models.Model):
	name = models.CharField(max_length=255)
	city = models.CharField(max_length=128)
	state = models.CharField(max_length=2, choices=US_STATES)
	latitude = models.DecimalField(max_digits=9, decimal_places=6)
	longitude = models.DecimalField(max_digits=9, decimal_places=6)

	class Meta:
		ordering = ["name"]

	def __str__(self) -> str:
		return f"{self.name} ({self.city}, {self.state})"


