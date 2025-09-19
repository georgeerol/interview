from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand

from core.models import Business


class Command(BaseCommand):
	help = "Export all businesses to businesses.json at the project root"

	def add_arguments(self, parser) -> None:
		parser.add_argument(
			"--output",
			dest="output",
			help="Path to output JSON file (default: businesses.json at project root)",
		)

	def handle(self, *args: Any, **options: Any) -> None:
		root_dir = Path(__file__).resolve().parents[4]
		output = options.get("output") or str(root_dir / "businesses.json")
		path = Path(output)
		path.parent.mkdir(parents=True, exist_ok=True)

		records = [
			{
				"name": b.name,
				"city": b.city,
				"state": b.state,
				"latitude": float(b.latitude),
				"longitude": float(b.longitude),
			}
			for b in Business.objects.all().iterator()
		]

		path.write_text(json.dumps(records, indent=2), encoding="utf-8")
		self.stdout.write(self.style.SUCCESS(f"Exported {len(records)} businesses to {path}"))


