#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
import shutil
from datetime import datetime
from opencc import OpenCC

from app import app
from models import db, Category, Product, Review, User

# 初始化转换器（简体 -> 香港繁体，您也可以改用 'zh-tw'）
cc = OpenCC('s2hk')  # s2tw 为台湾繁体

def convert_text(text):
    """将简体字符串转换为繁体，若为空或非字符串则原样返回"""
    if text and isinstance(text, str):
        return cc.convert(text)
    return text

def convert_json_fields(json_str):
    """转换 JSON 字符串内部的所有字符串值"""
    if not json_str:
        return json_str
    try:
        data = json.loads(json_str)
        if isinstance(data, dict):
            new_data = {}
            for k, v in data.items():
                # 转换键和值中的中文
                new_key = convert_text(k)
                if isinstance(v, str):
                    new_data[new_key] = convert_text(v)
                elif isinstance(v, dict):
                    new_data[new_key] = convert_json_fields(json.dumps(v))
                else:
                    new_data[new_key] = v
            return json.dumps(new_data, ensure_ascii=False)
        else:
            return json_str
    except:
        return json_str

def backup_db():
    """备份数据库文件"""
    db_path = 'pegasus.db'
    if os.path.exists(db_path):
        backup_name = f'pegasus_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
        shutil.copy(db_path, backup_name)
        print(f"✅ 数据库已备份至: {backup_name}")
        return backup_name
    else:
        print("⚠️ 未找到 pegasus.db，跳过备份")
        return None

def convert_database():
    print("🚀 开始转换数据库内容为繁体中文...")
    backup_db()

    with app.app_context():
        # 1. 转换分类
        categories = Category.query.all()
        for cat in categories:
            changed = False
            if cat.name:
                new_name = convert_text(cat.name)
                if new_name != cat.name:
                    cat.name = new_name
                    changed = True
            if cat.description:
                new_desc = convert_text(cat.description)
                if new_desc != cat.description:
                    cat.description = new_desc
                    changed = True
            if changed:
                print(f"  转换分类: {cat.name} (ID: {cat.id})")
        db.session.commit()
        print(f"✅ 完成 {len(categories)} 个分类的转换")

        # 2. 转换商品
        products = Product.query.all()
        for prod in products:
            changed = False
            if prod.name:
                new_name = convert_text(prod.name)
                if new_name != prod.name:
                    prod.name = new_name
                    changed = True
            if prod.short_description:
                new_short = convert_text(prod.short_description)
                if new_short != prod.short_description:
                    prod.short_description = new_short
                    changed = True
            if prod.description:
                new_desc = convert_text(prod.description)
                if new_desc != prod.description:
                    prod.description = new_desc
                    changed = True
            if prod.brand:
                new_brand = convert_text(prod.brand)
                if new_brand != prod.brand:
                    prod.brand = new_brand
                    changed = True
            if prod.specifications:
                new_spec = convert_json_fields(prod.specifications)
                if new_spec != prod.specifications:
                    prod.specifications = new_spec
                    changed = True
            if changed:
                print(f"  转换商品: {prod.name} (ID: {prod.id})")
        db.session.commit()
        print(f"✅ 完成 {len(products)} 个商品的转换")

        # 3. 转换评价
        reviews = Review.query.all()
        for rev in reviews:
            changed = False
            if rev.title:
                new_title = convert_text(rev.title)
                if new_title != rev.title:
                    rev.title = new_title
                    changed = True
            if rev.content:
                new_content = convert_text(rev.content)
                if new_content != rev.content:
                    rev.content = new_content
                    changed = True
            if changed:
                print(f"  转换评价: ID {rev.id}")
        db.session.commit()
        print(f"✅ 完成 {len(reviews)} 条评价的转换")

        # 4. 转换用户信息（可选，如需转换姓名/地址）
        users = User.query.all()
        for user in users:
            changed = False
            if user.first_name:
                new_fn = convert_text(user.first_name)
                if new_fn != user.first_name:
                    user.first_name = new_fn
                    changed = True
            if user.last_name:
                new_ln = convert_text(user.last_name)
                if new_ln != user.last_name:
                    user.last_name = new_ln
                    changed = True
            if user.address:
                new_addr = convert_text(user.address)
                if new_addr != user.address:
                    user.address = new_addr
                    changed = True
            if changed:
                print(f"  转换用户: {user.username} (ID: {user.id})")
        db.session.commit()
        print(f"✅ 完成 {len(users)} 个用户信息转换")

        print("\n🎉 所有数据转换完成！请重启应用查看效果。")

if __name__ == "__main__":
    convert_database()