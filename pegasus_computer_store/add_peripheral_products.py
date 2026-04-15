# add_peripheral_products.py
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

def add_peripheral_products():
    with app.app_context():
        peripheral_category = Category.query.filter_by(slug='peripheral').first()
        if not peripheral_category:
            print("❌ 未找到 '外設' 分類，嘗試創建...")
            peripheral_category = Category(name='外設', slug='peripheral', sort_order=9, is_active=True)
            db.session.add(peripheral_category)
            db.session.commit()
            print("✅ 已創建 外設 分類")

        products = [
            {
                "name": "Logitech G Pro X Superlight 2 無線鼠標",
                "brand": "Logitech",
                "price": 1099.00,
                "original_price": 1299.00,
                "stock": 30,
                "sku": "LOG-GPROX-SL2",
                "short_description": "60g超輕量，無線，HERO 2傳感器",
                "description": "電競級無線鼠標，約60g重量，32000 DPI，最長95小時續航。",
                "specifications": '{"重量":"60g","連接":"無線2.4GHz","DPI":"32000","按鍵":"5個","續航":"95小時"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "Keychron K2 Pro 機械鍵盤",
                "brand": "Keychron",
                "price": 699.00,
                "original_price": 799.00,
                "stock": 25,
                "sku": "KEY-K2-PRO",
                "short_description": "75%布局，藍牙/有線，熱插拔，Gasket結構",
                "description": "Mac/Win雙系統適配，RGB背光，K Pro軸體，QMK/VIA開源改鍵。",
                "specifications": '{"布局":"75%","連接":"藍牙5.1+有線","軸體":"熱插拔","電池":"4000mAh","鍵帽":"PBT雙色"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "HyperX Cloud II 電競耳機",
                "brand": "HyperX",
                "price": 599.00,
                "original_price": 699.00,
                "stock": 40,
                "sku": "HX-CLOUD-II",
                "short_description": "7.1虛擬環繞聲，53mm驅動單元",
                "description": "虛擬7.1環繞聲，53mm驅動單元，記憶海綿耳罩，可拆卸麥克風。",
                "specifications": '{"類型":"頭戴式","連接":"USB/3.5mm","驅動單元":"53mm","頻率":"15Hz-25kHz","重量":"320g"}',
                "is_featured": True,
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
                category_id=peripheral_category.id,
                is_featured=p["is_featured"],
                is_new=p["is_new"],
                is_active=True
            )
            db.session.add(product)
            added += 1
            print(f"✅ 已添加外設: {p['name']}")

        db.session.commit()
        print(f"\n🎉 成功添加 {added} 個外設商品！")

if __name__ == "__main__":
    add_peripheral_products()