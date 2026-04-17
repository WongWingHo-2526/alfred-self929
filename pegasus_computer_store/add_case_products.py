# add_case_products.py
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

def add_case_products():
    with app.app_context():
        # 查找機箱分類 (slug='case')
        case_category = Category.query.filter_by(slug='case').first()
        if not case_category:
            print("❌ 未找到 '機箱' 分類，嘗試創建...")
            case_category = Category(name='機箱', slug='case', sort_order=7, is_active=True)
            db.session.add(case_category)
            db.session.commit()
            print("✅ 已創建 機箱 分類")

        products = [
            {
                "name": "Lian Li O11 Dynamic EVO 白色",
                "brand": "Lian Li",
                "price": 1199.00,
                "original_price": 1399.00,
                "stock": 15,
                "sku": "LIANLI-O11D-EVO-WH",
                "short_description": "ATX海景房機箱，雙玻璃側板，支持背插主板",
                "description": "經典海景房機箱，可翻轉設計，支持E-ATX主板，360水冷，雙玻璃側透。",
                "specifications": '{"尺寸":"465x285x459mm","主板支持":"E-ATX/ATX/M-ATX","水冷支持":"頂部360/側面360","硬盤位":"4個","材質":"鋼化玻璃+SPCC"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "Fractal Design North 黑色 mesh",
                "brand": "Fractal Design",
                "price": 899.00,
                "original_price": 999.00,
                "stock": 20,
                "sku": "FD-NORTH-BK",
                "short_description": "ATX木紋面板機箱，優雅散熱",
                "description": "胡桃木/橡木前面板，開放式網孔，支持360水冷，鋼化玻璃側板。",
                "specifications": '{"尺寸":"447x215x469mm","主板支持":"ATX/M-ATX","水冷支持":"前360/頂240","硬盤位":"2個","材質":"木+鋼+玻璃"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "Thermaltake Versa H21 黑色",
                "brand": "Thermaltake",
                "price": 299.00,
                "original_price": 399.00,
                "stock": 40,
                "sku": "TT-VERSA-H21",
                "short_description": "ATX入門機箱，經濟實用",
                "description": "經典設計，支持ATX主板，前置USB 3.0，側透亞克力。",
                "specifications": '{"尺寸":"429x200x478mm","主板支持":"ATX/M-ATX","水冷支持":"後120","硬盤位":"3個","材質":"SPCC+亞克力"}',
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
                category_id=case_category.id,
                is_featured=p["is_featured"],
                is_new=p["is_new"],
                is_active=True
            )
            db.session.add(product)
            added += 1
            print(f"✅ 已添加機箱: {p['name']}")

        db.session.commit()
        print(f"\n🎉 成功添加 {added} 個機箱商品！")

if __name__ == "__main__":
    add_case_products()