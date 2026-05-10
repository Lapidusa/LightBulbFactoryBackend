from decimal import Decimal

from sqlalchemy.orm import Session

from services.product_service.models import Category, Product, ProductImage


def seed_catalog(db: Session) -> None:
    if db.query(Product).count() > 0:
        return

    categories = [
        Category(name="LED лампы", slug="led", description="Экономичные светодиодные лампы"),
        Category(name="Умные лампы", slug="smart", description="Лампы с управлением через приложение"),
        Category(name="Промышленные лампы", slug="industrial", description="Освещение для складов и цехов"),
        Category(name="Декоративные лампы", slug="decorative", description="Лампы для интерьерного света"),
    ]
    db.add_all(categories)
    db.flush()
    category_by_slug = {category.slug: category for category in categories}

    rows = [
        ("LB-LED-001", "LED A60 9W теплый свет", "led-a60-9w-warm", "led", 199, 9, "E27", 3000, 806, 15000, "Luma", "Home"),
        ("LB-LED-002", "LED A60 12W нейтральный свет", "led-a60-12w-neutral", "led", 249, 12, "E27", 4000, 1050, 20000, "Luma", "Home"),
        ("LB-LED-003", "LED Candle 7W теплый свет", "led-candle-7w-warm", "led", 179, 7, "E14", 3000, 560, 15000, "Luma", "Classic"),
        ("LB-LED-004", "LED Globe 10W матовая", "led-globe-10w-matte", "led", 329, 10, "E27", 4000, 900, 18000, "Brighton", "Globe"),
        ("LB-LED-005", "LED Spot GU10 6W", "led-spot-gu10-6w", "led", 219, 6, "GU10", 4000, 480, 20000, "Brighton", "Spot"),
        ("LB-LED-006", "LED MR16 5W", "led-mr16-5w", "led", 199, 5, "GU5.3", 3000, 420, 15000, "Brighton", "Spot"),
        ("LB-LED-007", "LED High Power 18W", "led-high-power-18w", "led", 459, 18, "E27", 6500, 1600, 25000, "Voltix", "Power"),
        ("LB-LED-008", "LED Filament 8W", "led-filament-8w", "decorative", 289, 8, "E27", 2700, 720, 15000, "Luma", "Retro"),
        ("LB-LED-009", "LED Filament Candle 6W", "led-filament-candle-6w", "decorative", 269, 6, "E14", 2700, 520, 15000, "Luma", "Retro"),
        ("LB-SMT-010", "Smart RGB 10W Wi-Fi", "smart-rgb-10w-wifi", "smart", 899, 10, "E27", 6500, 850, 25000, "SmartLux", "RGB"),
        ("LB-SMT-011", "Smart White 9W Wi-Fi", "smart-white-9w-wifi", "smart", 749, 9, "E27", 4000, 806, 25000, "SmartLux", "White"),
        ("LB-SMT-012", "Smart Candle RGB 6W", "smart-candle-rgb-6w", "smart", 799, 6, "E14", 6500, 500, 20000, "SmartLux", "RGB"),
        ("LB-IND-013", "Industrial E40 40W", "industrial-e40-40w", "industrial", 1290, 40, "E40", 5000, 4200, 30000, "Voltix", "Factory"),
        ("LB-IND-014", "Industrial E40 60W", "industrial-e40-60w", "industrial", 1690, 60, "E40", 5000, 6500, 30000, "Voltix", "Factory"),
        ("LB-IND-015", "Warehouse UFO 100W", "warehouse-ufo-100w", "industrial", 4990, 100, "hook", 5000, 12000, 50000, "Voltix", "UFO"),
        ("LB-IND-016", "Workshop Tube 18W", "workshop-tube-18w", "industrial", 390, 18, "G13", 4000, 1800, 25000, "Brighton", "Tube"),
        ("LB-DEC-017", "Decor Amber G95 6W", "decor-amber-g95-6w", "decorative", 449, 6, "E27", 2200, 420, 12000, "Luma", "Amber"),
        ("LB-DEC-018", "Decor Spiral ST64 5W", "decor-spiral-st64-5w", "decorative", 499, 5, "E27", 2200, 360, 12000, "Luma", "Amber"),
        ("LB-DEC-019", "Decor Globe G125 8W", "decor-globe-g125-8w", "decorative", 599, 8, "E27", 2700, 650, 15000, "Brighton", "Globe"),
        ("LB-SMT-020", "Smart Filament 7W", "smart-filament-7w", "smart", 990, 7, "E27", 2700, 650, 20000, "SmartLux", "Retro"),
    ]

    for index, row in enumerate(rows, start=1):
        sku, name, slug, category_slug, price, wattage, base_type, temp, flux, lifetime, brand, series = row
        product = Product(
            sku=sku,
            name=name,
            slug=slug,
            short_description=f"{name}: надежная лампа для дома, офиса или производства.",
            description=f"{name} серии {series}. Ресурс {lifetime} часов, стандартное напряжение 220 В.",
            category_id=category_by_slug[category_slug].id,
            price=Decimal(str(price)),
            stock_qty=20 + index,
            wattage=wattage,
            base_type=base_type,
            color_temperature=temp,
            luminous_flux=flux,
            voltage=220,
            lifetime_hours=lifetime,
            brand=brand,
            series=series,
            is_active=True,
        )
        product.images = [
            ProductImage(
                image_url=f"https://placehold.co/800x600?text={sku}",
                alt_text=name,
                sort_order=0,
                is_main=True,
            )
        ]
        db.add(product)

