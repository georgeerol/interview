from __future__ import annotations

from django.db import migrations
from pathlib import Path
import json


def seed_businesses(apps, schema_editor):
	Business = apps.get_model("core", "Business")

	# Read businesses.json from project root
	root_dir = Path(__file__).resolve().parents[2]
	json_path = root_dir / "businesses.json"
	if not json_path.exists():
		return

	try:
		data = json.loads(json_path.read_text(encoding="utf-8"))
	except Exception:
		return

	if not isinstance(data, list):
		return

	to_create = []
	for obj in data:
		try:
			name = str(obj.get("name", "")).strip()
			city = str(obj.get("city", "")).strip()
			state = str(obj.get("state", "")).strip()
			latitude = obj.get("latitude")
			longitude = obj.get("longitude")
			if not (name and city and state and latitude is not None and longitude is not None):
				continue
			to_create.append(
				Business(
					name=name,
					city=city,
					state=state,
					latitude=float(latitude),
					longitude=float(longitude),
				)
			)
		except Exception:
			continue

	if to_create:
		Business.objects.bulk_create(to_create, ignore_conflicts=True)


def unseed_businesses(apps, schema_editor):
	Business = apps.get_model("core", "Business")
	Business.objects.all().delete()


class Migration(migrations.Migration):

	dependencies = [
		("core", "0001_initial"),
	]

	operations = [
		migrations.RunPython(seed_businesses, unseed_businesses),
	]


