# add_ssd_products.py
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

def add_ssd_products():
    with app.app_context():
        ssd_category = Category.query.filter_by(slug='ssd').first()
        if not ssd_category:
            print("❌ 未找到 '固態硬盤' 分類，嘗試創建...")
            ssd_category = Category(name='固態硬盤', slug='ssd', sort_order=5, is_active=True)
            db.session.add(ssd_category)
            db.session.commit()
            print("✅ 已創建 固態硬盤 分類")

        products = [
            {
                "name": "Samsung 990 Pro 1TB NVMe PCIe 4.0",
                "brand": "Samsung",
                "price": 899.00,
                "original_price": 999.00,
                "stock": 30,
                "sku": "SAMSUNG-990PRO-1TB",
                "short_description": "1TB NVMe PCIe 4.0，讀取7450MB/s",
                "description": "頂級PCIe 4.0固態，順序讀取高達7450MB/s，寫入6900MB/s，適合遊戲和專業應用。",
                "specifications": '{"容量":"1TB","接口":"NVMe PCIe 4.0","讀取速度":"7450MB/s","寫入速度":"6900MB/s","緩存":"1GB DRAM"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "WD Black SN850X 2TB NVMe PCIe 4.0",
                "brand": "Western Digital",
                "price": 1299.00,
                "original_price": 1499.00,
                "stock": 25,
                "sku": "WD-SN850X-2TB",
                "short_description": "2TB NVMe PCIe 4.0，讀取7300MB/s",
                "description": "高性能遊戲固態，順序讀取7300MB/s，支持遊戲模式2.0。",
                "specifications": '{"容量":"2TB","接口":"NVMe PCIe 4.0","讀取速度":"7300MB/s","寫入速度":"6600MB/s","緩存":"2GB DRAM"}',
                "is_featured": True,
                "is_new": True
            },
            {
                "name": "Kingston KC3000 512GB NVMe PCIe 4.0",
                "brand": "Kingston",
                "price": 499.00,
                "original_price": 599.00,
                "stock": 50,
                "sku": "KING-KC3000-512G",
                "short_description": "512GB NVMe PCIe 4.0，讀取7000MB/s",
                "description": "入門級PCIe 4.0固態，性價比高，適合系統盤。",
                "specifications": '{"容量":"512GB","接口":"NVMe PCIe 4.0","讀取速度":"7000MB/s","寫入速度":"3900MB/s","緩存":"無DRAM（HMB）"}',
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
                category_id=ssd_category.id,
                is_featured=p["is_featured"],
                is_new=p["is_new"],
                is_active=True
            )
            db.session.add(product)
            added += 1
            print(f"✅ 已添加固態硬盤: {p['name']}")

        db.session.commit()
        print(f"\n🎉 成功添加 {added} 個固態硬盤商品！")

if __name__ == "__main__":
    add_ssd_products()