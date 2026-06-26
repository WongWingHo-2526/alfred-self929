# seed.py
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from add_cpu_products import add_cpu_products
from add_gpu_products import add_gpu_products
from add_motherboard_products import add_motherboard_products
from add_ram_products import add_ram_products
from add_ssd_products import add_ssd_products
from add_psu_products import add_psu_products
from add_case_products import add_case_products
from add_cooler_products import add_cooler_products
from add_peripheral_products import add_peripheral_products

if __name__ == "__main__":
    print("Beginning batch data seeding into AWS RDS MySQL...")
    with app.app_context():
        # 1. Double check that the empty tables are physically created on RDS
        db.create_all()
        
        # 2. Fire your sample data loader functions one-by-one
        try:
            add_cpu_products()
            add_gpu_products()
            add_motherboard_products()
            add_ram_products()
            add_ssd_products()
            add_psu_products()
            add_case_products()
            add_cooler_products()
            add_peripheral_products()
            print("All sample product records have been securely loaded into AWS!")
        except Exception as e:
            print(f"Data seeding failed: {e}")