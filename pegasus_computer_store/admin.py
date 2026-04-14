from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from models import db, User, Product, Category, Order, OrderItem, Review
from forms import ProductForm

admin_bp = Blueprint('admin', __name__)

def admin_required(func):
    """管理员权限装饰器"""
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return func(*args, **kwargs)
    wrapper.__name__ = func.__name__
    return wrapper

@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    total_users = User.query.count()
    total_products = Product.query.count()
    total_orders = Order.query.count()
    pending_orders = Order.query.filter_by(status='pending').count()
    
    # 最近订单
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(10).all()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_products=total_products,
                         total_orders=total_orders,
                         pending_orders=pending_orders,
                         recent_orders=recent_orders)

@admin_bp.route('/products')
@login_required
@admin_required
def admin_products():
    products = Product.query.order_by(Product.created_at.desc()).all()
    return render_template('admin/products.html', products=products)

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.sort_order).all()]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            slug=form.slug.data,
            description=form.description.data,
            short_description=form.short_description.data,
            price=form.price.data,
            original_price=form.original_price.data,
            stock=form.stock.data,
            sku=form.sku.data,
            brand=form.brand.data,
            specifications=form.specifications.data,
            category_id=form.category_id.data,
            is_featured=form.is_featured.data,
            is_new=form.is_new.data,
            is_active=form.is_active.data
        )
        db.session.add(product)
        db.session.commit()
        flash('商品添加成功', 'success')
        return redirect(url_for('admin.admin_products'))
    
    return render_template('admin/product_form.html', form=form, title='添加商品')

@admin_bp.route('/products/edit/<int:product_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.order_by(Category.sort_order).all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.slug = form.slug.data
        product.description = form.description.data
        product.short_description = form.short_description.data
        product.price = form.price.data
        product.original_price = form.original_price.data
        product.stock = form.stock.data
        product.sku = form.sku.data
        product.brand = form.brand.data
        product.specifications = form.specifications.data
        product.category_id = form.category_id.data
        product.is_featured = form.is_featured.data
        product.is_new = form.is_new.data
        product.is_active = form.is_active.data
        db.session.commit()
        flash('商品更新成功', 'success')
        return redirect(url_for('admin.admin_products'))
    
    return render_template('admin/product_form.html', form=form, title='编辑商品', product=product)

@admin_bp.route('/products/delete/<int:product_id>')
@login_required
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('商品已删除', 'success')
    return redirect(url_for('admin.admin_products'))

@admin_bp.route('/users')
@login_required
@admin_required
def admin_users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@admin_bp.route('/users/toggle/<int:user_id>')
@login_required
@admin_required
def toggle_user(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('不能禁用自己', 'danger')
        return redirect(url_for('admin.admin_users'))
    user.is_active = not user.is_active
    db.session.commit()
    flash(f'用户 {user.username} 状态已更新', 'success')
    return redirect(url_for('admin.admin_users'))

@admin_bp.route('/orders')
@login_required
@admin_required
def admin_orders():
    orders = Order.query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=orders)

@admin_bp.route('/orders/update/<int:order_id>/<status>')
@login_required
@admin_required
def update_order_status(order_id, status):
    order = Order.query.get_or_404(order_id)
    valid_status = ['pending', 'paid', 'shipped', 'delivered', 'cancelled']
    if status in valid_status:
        order.status = status
        if status == 'paid':
            from datetime import datetime
            order.paid_at = datetime.utcnow()
        elif status == 'shipped':
            order.shipped_at = datetime.utcnow()
        elif status == 'delivered':
            order.delivered_at = datetime.utcnow()
        db.session.commit()
        flash(f'订单 #{order.order_number} 状态已更新为 {status}', 'success')
    return redirect(url_for('admin.admin_orders'))

@admin_bp.route('/categories')
@login_required
@admin_required
def admin_categories():
    categories = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=categories)

@admin_bp.route('/categories/add', methods=['POST'])
@login_required
@admin_required
def add_category():
    name = request.form.get('name')
    slug = request.form.get('slug')
    if name and slug:
        category = Category(name=name, slug=slug, sort_order=Category.query.count())
        db.session.add(category)
        db.session.commit()
        flash('分类添加成功', 'success')
    return redirect(url_for('admin.admin_categories'))

@admin_bp.route('/categories/delete/<int:category_id>')
@login_required
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.products:
        flash('该分类下有商品，无法删除', 'danger')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('分类已删除', 'success')
    return redirect(url_for('admin.admin_categories'))