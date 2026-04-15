# add_cooler_products.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app
from models import db, Category, Product

def slugify(name):
    import re
    slug = name.lower()
    slug = re.sub(r'[^\w\-]+', '-', slug)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug

def add_cooler_products():
    with app.app_context():
        cooler_category = Category.query.filter_by(slug='cooler').first()
        if not cooler_category:
            print("❌ 未找到 '散熱器' 分類，嘗試創建...")
            cooler_category = Category(name='散熱器', slug='cooler', sort_order=8, is_active=True)
            db.session.add(cooler_category)
            db.session.commit()
            print("✅ 已創建 散熱器 分類")

        products = [
            {
                "name": "NZXT Kraken Elite 360 RGB",
                "brand": "NZXT",
                "price": 1899.00,
                "original_price": 2099.00,
                "stock": 12,
                "sku": "NZXT-KRAKEN-360",
                "short_description": "360mm一體水冷，2.36英寸LCD屏幕，RGB風扇",
                "description": "高性能一體水冷，可自定義LCD顯示屏，顯示溫度/系統信息，高效散熱。",
                "specifications": '{"類型":"360mm一體水冷","風扇":"3x120mm RGB","轉速":"500-1800 RPM","水泵":"Asetek 7代","支持平台":"Intel LGA1700/1200, AMD AM5/AM4"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "Noctua NH-D15 chromax.black",
                "brand": "Noctua",
                "price": 799.00,
                "original_price": 899.00,
                "stock": 25,
                "sku": "NOCTUA-NHD15",
                "short_description": "雙塔風冷，6熱管，靜音風扇",
                "description": "旗艦風冷，雙塔設計，雙NF-A15風扇，頂級散熱性能，六年質保。",
                "specifications": '{"類型":"雙塔風冷","熱管":"6根","風扇":"2x140mm","高度":"165mm","TDP":"220W+","支持平台":"Intel/AMD主流"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "Thermalright Peerless Assassin 120 SE",
                "brand": "Thermalright",
                "price": 299.00,
                "original_price": 399.00,
                "stock": 50,
                "sku": "TL-PA120-SE",
                "short_description": "雙塔風冷，6熱管，性價比之王",
                "description": "入門級雙塔風冷，逆重力熱管，TL-C12C風扇，壓制i5/R5無壓力。",
                "specifications": '{"類型":"雙塔風冷","熱管":"6根","風扇":"2x120mm","高度":"155mm","TDP":"245W","支持平台":"Intel LGA1700/1200, AMD AM5/AM4"}',
                "is_featured": False,
                "is_new": False
            }
        ]

        added = 0
        for p in products:
            existing = Product.query.filter_by(sku=p["sku"]).first()
            if existing:
                print(f"⏭️ 已存在: {p['name']}")
                continue
            product = Product(
                name=p["name"],
                slug=slugify(p["name"]),
                brand=p["brand"],
                price=p["price"],
                original_price=p["original_price"],
                stock=p["stock"],
                sku=p["sku"],
                short_description=p["short_description"],
                description=p["description"],
                specifications=p["specifications"],
                category_id=cooler_category.id,
                is_featured=p["is_featured"],
                is_new=p["is_new"],
                is_active=True
            )
            db.session.add(product)
            added += 1
            print(f"✅ 已添加散熱器: {p['name']}")

        db.session.commit()
        print(f"\n🎉 成功添加 {added} 個散熱器商品！")

if __name__ == "__main__":
    add_cooler_products()