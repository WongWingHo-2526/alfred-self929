# add_gpu_products.py
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

def add_gpu_products():
    with app.app_context():
        gpu_category = Category.query.filter_by(slug='gpu').first()
        if not gpu_category:
            print("❌ 未找到 '顯卡' 分類，請檢查數據庫")
            return

        products = [
            {
                "name": "NVIDIA GeForce RTX 4090",
                "brand": "NVIDIA",
                "price": 15999.00,
                "original_price": 16999.00,
                "stock": 8,
                "sku": "NVIDIA-RTX4090",
                "short_description": "24GB GDDR6X，DLSS 3，旗艦遊戲顯卡",
                "description": "NVIDIA Ada Lovelace架構，16384個CUDA核心，24GB GDDR6X顯存。",
                "specifications": '{"顯存":"24GB GDDR6X","核心":"16384","功耗":"450W"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "NVIDIA GeForce RTX 4070 Ti",
                "brand": "NVIDIA",
                "price": 6999.00,
                "original_price": 7499.00,
                "stock": 15,
                "sku": "NVIDIA-RTX4070TI",
                "short_description": "12GB GDDR6X，高性能2K遊戲卡",
                "description": "適合1440p高刷新率遊戲，支持DLSS 3。",
                "specifications": '{"顯存":"12GB GDDR6X","核心":"7680","功耗":"285W"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "AMD Radeon RX 7900 XTX",
                "brand": "AMD",
                "price": 8999.00,
                "original_price": 9999.00,
                "stock": 12,
                "sku": "AMD-RX7900XTX",
                "short_description": "24GB GDDR6，RDNA 3架構",
                "description": "AMD旗艦顯卡，支持AV1編碼，適合4K遊戲。",
                "specifications": '{"顯存":"24GB GDDR6","核心":"6144","功耗":"355W"}',
                "is_featured": True,
                "is_new": True
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
                category_id=gpu_category.id,
                is_featured=p["is_featured"],
                is_new=p["is_new"],
                is_active=True
            )
            db.session.add(product)
            added += 1
            print(f"✅ 已添加顯卡: {p['name']}")

        db.session.commit()
        print(f"\n🎉 成功添加 {added} 個顯卡商品！")

if __name__ == "__main__":
    add_gpu_products()