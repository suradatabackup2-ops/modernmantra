"""
Seed the Package catalog with the 16 trips from the original
modernmantra-v10 static site.

Usage:
    python manage.py seed_packages           # add only missing packages
    python manage.py seed_packages --reset   # delete all packages first

This is idempotent — running it twice does NOT create duplicates.
Existing packages with the same name are left untouched (unless --reset).
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from apps.catalog.models import Package


# Pulled directly from the original modernmantra-v10 packages.html.
# Each tuple: (name, price_inr, days, nights, category_key, featured?, short_desc)
PACKAGES = [
    # ── Featured Himalayan ────────────────────────────────────────────
    (
        "Spiti Valley – Summer Escape", 19500, 7, 6, "trek", True,
        "High-altitude Himalayan circuit through Kaza, Key Monastery, "
        "Chandratal and Hikkim — the world's highest post office.",
    ),
    (
        "Zanskar Valley Road Trip", 34500, 9, 8, "road", True,
        "Delhi → Manali → Shinku La Pass → Gonbo Rangjon → Phuktal "
        "Monastery → Padum → Drang Drung Glacier → Jispa → Delhi. "
        "One of India's most remote adventures.",
    ),
    (
        "Manali Weekend Escape", 8500, 3, 2, "weekend", True,
        "Hadimba Temple, Mall Road, Vashisht hot springs, Solang Valley "
        "snow activities, drive through Atal Tunnel to Sissu. "
        "Perfect long-weekend from Delhi.",
    ),
    (
        "Manali–Kasol–Manikaran 6D", 11500, 6, 5, "trek", True,
        "Complete Himachal — Manali sightseeing, Solang Valley, Kullu "
        "river rafting, paragliding at Dobhi, Kasol riverside cafés, "
        "Manikaran hot springs & Gurudwara.",
    ),

    # ── Ladakh ────────────────────────────────────────────────────────
    (
        "Ladakh – Nubra & Pangong 5D", 22000, 5, 4, "trek", True,
        "Leh arrival & acclimatization → Sham Valley → Nubra via "
        "Khardung-La (5,359m) → Hunder sand dunes → Pangong Tso → "
        "Chang-La → Leh.",
    ),

    # ── Rajasthan ─────────────────────────────────────────────────────
    (
        "Rajasthan Grand Tour 9D", 30400, 9, 8, "road", False,
        "Jaipur (2N) → Jaisalmer desert camp (2N) → Jodhpur (1N) → "
        "Chittorgarh Fort enroute → Udaipur (3N). Private Innova "
        "Crysta throughout.",
    ),

    # ── South India ───────────────────────────────────────────────────
    (
        "Munnar Getaway 3D", 9500, 3, 2, "weekend", False,
        "Rose Garden → Mattupetty Tea Factory → Echo Point → Viripara "
        "Waterfalls → Tribal village → Kolukkumalai offroad jeep "
        "safari → Gap Road tea plantation drive.",
    ),
    (
        "Goa Holiday 5D", 8640, 5, 4, "backpack", False,
        "Arrival → Evening sunset cruise dinner → North Goa (Baga, "
        "Calangute, Anjuna, Fort Aguada) → South Goa (Colva, Miramar, "
        "Dona Paula, Old Goa Churches) → Leisure day → Departure.",
    ),
    (
        "Hyderabad Heritage Tour 5D", 16200, 5, 4, "backpack", False,
        "Birla Mandir, NTR Garden → Full day Ramoji Film City → "
        "Charminar, Chowmahalla Palace, Salar Jung Museum → Golconda "
        "Fort, Qutub Shahi Tombs.",
    ),

    # ── International ─────────────────────────────────────────────────
    (
        "Mauritius 6D Escape", 70000, 6, 5, "intl", True,
        "Catamaran sunset cruise → 5 Islands BBQ tour with snorkelling "
        "& dolphin watching → South tour (Chamarel, Seven Coloured "
        "Earth) → Casela World of Adventures.",
    ),
    (
        "Sri Lanka Heritage Tour 5D", 35300, 5, 4, "intl", False,
        "Colombo → Pinnawela Elephant Orphanage → Kandy (Temple of "
        "the Tooth) → Nuwara Eliya tea factory → Bentota golden "
        "beaches → Lotus Tower.",
    ),

    # ── Spiritual ─────────────────────────────────────────────────────
    (
        "Varanasi Spiritual Tour 3D", 6500, 3, 2, "weekend", False,
        "Evening Dashashwamedh Ghat Ganga Aarti → Early morning "
        "Ganges boat ride → Kashi Vishwanath Temple → Sarnath "
        "Buddhist site.",
    ),

    # ── Sikkim ────────────────────────────────────────────────────────
    (
        "Sikkim–Darjeeling 6D", 16500, 6, 5, "trek", False,
        "NJP/Bagdogra → Gangtok → Tsomgo Lake (12,000 ft) & Baba "
        "Mandir → Darjeeling → 4AM Tiger Hill sunrise over "
        "Kangchenjunga → Tea garden walk.",
    ),

    # ── Treks ─────────────────────────────────────────────────────────
    (
        "Kedarkantha Trek 5D", 5999, 5, 4, "trek", False,
        "Dehradun → Sankri → Juda Ka Talab → Kedarkantha Base → "
        "Summit (12,500 ft) → Hargaon → Sankri. Easy-moderate "
        "Himalayan trek. Best Nov–April.",
    ),
    (
        "Chandrakhani Pass Trek 5D", 4499, 5, 4, "trek", False,
        "Dhobi → Modernmantra Farm Stay (Dhara) → Rumshu → "
        "Chandrakhani Pass top → ancient Malana Village descent. "
        "Perfect intro trek.",
    ),
    (
        "Hampta Pass + Chandratal Trek 5D", 7500, 5, 4, "trek", True,
        "Manali → Chika → Balu Ka Ghera → Hampta Pass (14,100 ft) → "
        "Sheagoru → Chatru → Chandratal Lake & back. Classic "
        "crossover trek from green Kullu to barren Spiti.",
    ),
]


class Command(BaseCommand):
    help = "Seed the Package catalog with the 16 trips from the original site."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Delete all existing packages before seeding. DESTRUCTIVE.",
        )
        parser.add_argument(
            "--update",
            action="store_true",
            help="Update existing packages with the latest values from this file.",
        )

    def handle(self, *args, **opts):
        if opts["reset"]:
            count = Package.objects.count()
            Package.objects.all().delete()
            self.stdout.write(self.style.WARNING(f"Deleted {count} existing packages."))

        created = 0
        updated = 0
        skipped = 0

        for order_idx, (name, price, days, nights, category, featured, desc) in enumerate(PACKAGES, start=1):
            defaults = {
                "slug": slugify(name)[:140],
                "category": category,
                "price": price,
                "duration_days": days,
                "duration_nights": nights,
                "short_description": desc,
                "is_active": True,
                "is_featured": featured,
                "coming_soon": False,
                "display_order": order_idx * 10,  # 10, 20, 30 — leaves room for inserts
                "data_trip": name,  # matches data-trip HTML attribute exactly
            }

            obj, was_created = Package.objects.get_or_create(
                name=name,
                defaults=defaults,
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  + Created: {name}"))
            elif opts["update"]:
                for field, value in defaults.items():
                    setattr(obj, field, value)
                obj.save()
                updated += 1
                self.stdout.write(f"  ~ Updated: {name}")
            else:
                skipped += 1
                self.stdout.write(f"  · Already exists, skipped: {name}")

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS(
            f"Done. Created: {created}, Updated: {updated}, "
            f"Skipped (already existed): {skipped}, Total in DB: {Package.objects.count()}"
        ))
        if not opts["update"] and skipped:
            self.stdout.write(self.style.WARNING(
                "Tip: re-run with --update to refresh prices/descriptions of existing packages."
            ))
