from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, Product, Category, CartItem, Order, OrderItem, Review, BrowseHistory, Wishlist
from forms import RegistrationForm, LoginForm, ProductForm, CartUpdateForm, CheckoutForm, ProfileForm
from config import Config
from admin import admin_bp
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
import json

app = Flask(__name__)
app.config.from_object(Config)

# 初始化扩展
db.init_app(app)

# Flask-Login配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '请先登录'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注册后台管理蓝图
app.register_blueprint(admin_bp, url_prefix='/admin')

# 创建数据库表
with app.app_context():
    db.create_all()
    # 创建默认分类
    if Category.query.count() == 0:
        default_categories = [
            ('cpu', 'CPU处理器', 1),
            ('gpu', '显卡', 2),
            ('motherboard', '主板', 3),
            ('ram', '内存', 4),
            ('ssd', '固态硬盘', 5),
            ('psu', '电源', 6),
            ('case', '机箱', 7),
            ('cooler', '散热器', 8),
            ('peripheral', '外设', 9),
        ]
        for slug, name, order in default_categories:
            cat = Category(name=name, slug=slug, sort_order=order, is_active=True)
            db.session.add(cat)
        
        # 创建管理员用户（密码: admin123）
        admin = User(
            username='admin',
            email='admin@pegasus.com',
            first_name='Admin',
            last_name='User',
            is_admin=True,
            is_active=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

# ============= 辅助函数 =============
def save_uploaded_file(file):
    if file and file.filename:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(filepath)
        return unique_filename
    return None

def get_cart_count():
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    else:
        cart = session.get('cart', {})
        return sum(cart.values())

def get_cart_items():
    items = []
    total = 0
    
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in cart_items:
            subtotal = item.product.price * item.quantity
            total += subtotal
            items.append({
                'id': item.id,
                'product': item.product,
                'quantity': item.quantity,
                'subtotal': subtotal
            })
    else:
        cart = session.get('cart', {})
        for product_id, quantity in cart.items():
            product = Product.query.get(int(product_id))
            if product:
                subtotal = product.price * quantity
                total += subtotal
                items.append({
                    'id': f"session_{product_id}",
                    'product': product,
                    'quantity': quantity,
                    'subtotal': subtotal
                })
    
    return items, total

def merge_cart():
    """登录时合并session购物车到数据库"""
    if current_user.is_authenticated:
        session_cart = session.pop('cart', {})
        for product_id, quantity in session_cart.items():
            cart_item = CartItem.query.filter_by(
                user_id=current_user.id, 
                product_id=int(product_id)
            ).first()
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(
                    user_id=current_user.id,
                    product_id=int(product_id),
                    quantity=quantity
                )
                db.session.add(cart_item)
        db.session.commit()

# ============= 页面路由 =============
@app.route('/')
def index():
    # 获取推荐商品和新品
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    new_products = Product.query.filter_by(is_new=True, is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    
    # 最近浏览（Cookie）
    recent_product_ids = request.cookies.get('recent_products', '')
    recent_products = []
    if recent_product_ids:
        ids = [int(id) for id in recent_product_ids.split(',') if id.isdigit()]
        recent_products = Product.query.filter(Product.id.in_(ids), Product.is_active==True).limit(5).all()
    
    return render_template('index.html', 
                         featured_products=featured_products,
                         new_products=new_products,
                         categories=categories,
                         recent_products=recent_products,
                         cart_count=get_cart_count())

@app.route('/products')
def products():
    page = request.args.get('page', 1, type=int)
    category_slug = request.args.get('category', '')
    search = request.args.get('search', '')
    sort = request.args.get('sort', 'newest')
    
    query = Product.query.filter_by(is_active=True)
    
    if category_slug:
        category = Category.query.filter_by(slug=category_slug, is_active=True).first()
        if category:
            query = query.filter_by(category_id=category.id)
    
    if search:
        query = query.filter(Product.name.contains(search) | Product.brand.contains(search))
    
    if sort == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort == 'name_asc':
        query = query.order_by(Product.name.asc())
    else:
        query = query.order_by(Product.created_at.desc())
    
    pagination = query.paginate(page=page, per_page=app.config['PRODUCTS_PER_PAGE'], error_out=False)
    products = pagination.items
    
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    
    return render_template('products.html',
                         products=products,
                         pagination=pagination,
                         categories=categories,
                         current_category=category_slug,
                         search=search,
                         sort=sort,
                         cart_count=get_cart_count())

@app.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # 增加浏览次数
    product.view_count += 1
    db.session.commit()
    
    # 记录浏览历史（Cookie）
    recent_ids = request.cookies.get('recent_products', '')
    ids_list = [str(product.id)] + [id for id in recent_ids.split(',') if id and id != str(product.id)]
    recent_products_cookie = ','.join(ids_list[:10])
    
    # 登录用户记录浏览历史到数据库
    if current_user.is_authenticated:
        history = BrowseHistory.query.filter_by(
            user_id=current_user.id, 
            product_id=product.id
        ).first()
        if history:
            history.viewed_at = datetime.utcnow()
        else:
            history = BrowseHistory(user_id=current_user.id, product_id=product.id)
            db.session.add(history)
        db.session.commit()
    
    # 获取同分类其他商品
    related_products = Product.query.filter_by(
        category_id=product.category_id, 
        is_active=True
    ).filter(Product.id != product.id).limit(6).all()
    
    # 获取商品评价
    reviews = Review.query.filter_by(product_id=product.id, is_active=True).order_by(Review.created_at.desc()).all()
    
    response = make_response(render_template('product_detail.html',
                                            product=product,
                                            related_products=related_products,
                                            reviews=reviews,
                                            cart_count=get_cart_count()))
    response.set_cookie('recent_products', recent_products_cookie, max_age=30*24*3600)
    return response

@app.route('/cart')
def cart():
    items, total = get_cart_items()
    return render_template('cart.html', cart_items=items, total=total, cart_count=get_cart_count())

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = request.form.get('quantity', 1, type=int)
    product = Product.query.get_or_404(product_id)
    
    if quantity > product.stock:
        flash(f'库存不足，仅剩 {product.stock} 件', 'danger')
        return redirect(request.referrer or url_for('product_detail', slug=product.slug))
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            if cart_item.quantity + quantity > product.stock:
                flash(f'库存不足，仅剩 {product.stock} 件', 'danger')
                return redirect(request.referrer or url_for('product_detail', slug=product.slug))
            cart_item.quantity += quantity
        else:
            cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
            db.session.add(cart_item)
        db.session.commit()
    else:
        cart = session.get('cart', {})
        current_qty = cart.get(str(product_id), 0)
        if current_qty + quantity > product.stock:
            flash(f'库存不足，仅剩 {product.stock} 件', 'danger')
            return redirect(request.referrer or url_for('product_detail', slug=product.slug))
        cart[str(product_id)] = current_qty + quantity
        session['cart'] = cart
    
    flash(f'已添加 {product.name} 到购物车', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity = request.form.get('quantity', 1, type=int)
    
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id != current_user.id:
            flash('无权操作', 'danger')
            return redirect(url_for('cart'))
        if quantity <= 0:
            db.session.delete(cart_item)
        else:
            cart_item.quantity = quantity
        db.session.commit()
    else:
        cart = session.get('cart', {})
        if quantity <= 0:
            cart.pop(str(item_id), None)
        else:
            cart[str(item_id)] = quantity
        session['cart'] = cart
    
    flash('购物车已更新', 'success')
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>')
def remove_from_cart(item_id):
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id == current_user.id:
            db.session.delete(cart_item)
            db.session.commit()
    else:
        cart = session.get('cart', {})
        cart.pop(str(item_id), None)
        session['cart'] = cart
    
    flash('已从购物车移除', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items, total = get_cart_items()
    if not items:
        flash('购物车为空', 'warning')
        return redirect(url_for('products'))
    
    form = CheckoutForm()
    
    if form.validate_on_submit():
        # 生成订单号
        order_number = f"PEG{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}"
        
        order = Order(
            order_number=order_number,
            user_id=current_user.id,
            total_amount=total,
            shipping_name=form.shipping_name.data,
            shipping_phone=form.shipping_phone.data,
            shipping_address=form.shipping_address.data,
            note=form.note.data,
            status='pending'
        )
        db.session.add(order)
        db.session.flush()
        
        # 创建订单项并更新库存
        for item in items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item['product'].id,
                product_name=item['product'].name,
                product_price=item['product'].price,
                quantity=item['quantity'],
                subtotal=item['subtotal']
            )
            db.session.add(order_item)
            
            # 扣减库存
            item['product'].stock -= item['quantity']
        
        # 清空购物车
        if current_user.is_authenticated:
            CartItem.query.filter_by(user_id=current_user.id).delete()
        else:
            session.pop('cart', None)
        
        db.session.commit()
        
        flash(f'订单已提交，订单号: {order_number}', 'success')
        return redirect(url_for('order_detail', order_id=order.id))
    
    # 预填用户信息
    if request.method == 'GET':
        form.shipping_name.data = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.username
        form.shipping_phone.data = current_user.phone
        form.shipping_address.data = current_user.address
    
    return render_template('checkout.html', form=form, cart_items=items, total=total, cart_count=get_cart_count())

@app.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    pagination = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).paginate(
        page=page, per_page=app.config['ORDERS_PER_PAGE'], error_out=False
    )
    orders = pagination.items
    return render_template('orders.html', orders=orders, pagination=pagination, cart_count=get_cart_count())

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('无权查看此订单', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order, cart_count=get_cart_count())

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        username = form.username.data
        user = User.query.filter((User.username == username) | (User.email == username)).first()
        
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('账号已被禁用', 'danger')
                return redirect(url_for('login'))
            
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            user.login_count += 1
            db.session.commit()
            
            # 合并购物车
            merge_cart()
            
            next_page = request.args.get('next')
            flash(f'欢迎回来，{user.username}！', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('用户名或密码错误', 'danger')
    
    return render_template('login.html', form=form, cart_count=get_cart_count())

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash('注册成功！欢迎加入飛馬電腦', 'success')
        return redirect(url_for('index'))
    
    return render_template('register.html', form=form, cart_count=get_cart_count())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登录', 'info')
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = ProfileForm()
    if form.validate_on_submit():
        current_user.first_name = form.first_name.data
        current_user.last_name = form.last_name.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        db.session.commit()
        flash('个人资料已更新', 'success')
        return redirect(url_for('profile'))
    
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.address.data = current_user.address
    
    return render_template('profile.html', form=form, cart_count=get_cart_count())

@app.route('/api/cart/count')
def api_cart_count():
    return jsonify({'count': get_cart_count()})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)