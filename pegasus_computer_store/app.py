# app.py - 完整版，包含所有路由和輔助函數
import os
import uuid
import json
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import db, User, Product, Category, CartItem, Order, OrderItem, Review, BrowseHistory, Wishlist
from forms import RegistrationForm, LoginForm, ProductForm, CartUpdateForm, CheckoutForm, ProfileForm
from config import Config
from admin import admin_bp

app = Flask(__name__)
app.config.from_object(Config)

# 初始化數據庫
db.init_app(app)

# Flask-Login 配置
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = '請先登錄'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 注冊後台藍圖
app.register_blueprint(admin_bp, url_prefix='/admin')

# ---------- 自定義 Jinja2 過濾器 ----------
@app.template_filter('from_json')
def from_json_filter(value):
    """將 JSON 字符串解析為 Python 字典"""
    try:
        return json.loads(value) if value else {}
    except:
        return {}

# ---------- 購物車輔助函數 ----------
def get_cart_count():
    """獲取購物車商品總數"""
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    else:
        cart = session.get('cart', {})
        return sum(cart.values())

def get_cart_items():
    """獲取購物車詳情和總金額"""
    items = []
    total = 0
    if current_user.is_authenticated:
        cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in cart_items:
            if item.product and item.product.is_active:
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
            if product and product.is_active:
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
    """登錄時合並session購物車到數據庫"""
    if current_user.is_authenticated:
        session_cart = session.pop('cart', {})
        for product_id, quantity in session_cart.items():
            product_id = int(product_id)
            cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(user_id=current_user.id, product_id=product_id, quantity=quantity)
                db.session.add(cart_item)
        db.session.commit()

# ---------- 首頁路由 ----------
@app.route('/')
def index():
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(8).all()
    new_products = Product.query.filter_by(is_new=True, is_active=True).order_by(Product.created_at.desc()).limit(8).all()
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    # 最近瀏覽（Cookie）
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

# ---------- 商品列表 ----------
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

# ---------- 商品詳情 ----------
@app.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    product.view_count += 1
    db.session.commit()
    # 記錄瀏覽歷史（Cookie）
    recent_ids = request.cookies.get('recent_products', '')
    ids_list = [str(product.id)] + [id for id in recent_ids.split(',') if id and id != str(product.id)]
    recent_products_cookie = ','.join(ids_list[:10])
    if current_user.is_authenticated:
        history = BrowseHistory.query.filter_by(user_id=current_user.id, product_id=product.id).first()
        if history:
            history.viewed_at = datetime.utcnow()
        else:
            history = BrowseHistory(user_id=current_user.id, product_id=product.id)
            db.session.add(history)
        db.session.commit()
    related_products = Product.query.filter_by(category_id=product.category_id, is_active=True).filter(Product.id != product.id).limit(6).all()
    reviews = Review.query.filter_by(product_id=product.id, is_active=True).order_by(Review.created_at.desc()).all()
    response = make_response(render_template('product_detail.html',
                                            product=product,
                                            related_products=related_products,
                                            reviews=reviews,
                                            cart_count=get_cart_count()))
    response.set_cookie('recent_products', recent_products_cookie, max_age=30*24*3600)
    return response

# ---------- 購物車 ----------
@app.route('/cart')
def cart():
    items, total = get_cart_items()
    return render_template('cart.html', cart_items=items, total=total, cart_count=get_cart_count())

@app.route('/cart/add/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    quantity = request.form.get('quantity', 1, type=int)
    product = Product.query.get_or_404(product_id)
    if quantity > product.stock:
        flash(f'庫存不足，僅剩 {product.stock} 件', 'danger')
        return redirect(request.referrer or url_for('product_detail', slug=product.slug))
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
        if cart_item:
            if cart_item.quantity + quantity > product.stock:
                flash(f'庫存不足，僅剩 {product.stock} 件', 'danger')
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
            flash(f'庫存不足，僅剩 {product.stock} 件', 'danger')
            return redirect(request.referrer or url_for('product_detail', slug=product.slug))
        cart[str(product_id)] = current_qty + quantity
        session['cart'] = cart
    flash(f'已添加 {product.name} 到購物車', 'success')
    return redirect(request.referrer or url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    quantity = request.form.get('quantity', 1, type=int)
    if current_user.is_authenticated:
        cart_item = CartItem.query.get_or_404(item_id)
        if cart_item.user_id != current_user.id:
            flash('無權操作', 'danger')
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
    flash('購物車已更新', 'success')
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
    flash('已從購物車移除', 'success')
    return redirect(url_for('cart'))

# ---------- 結賬和訂單 ----------
@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    items, total = get_cart_items()
    if not items:
        flash('購物車為空', 'warning')
        return redirect(url_for('products'))
    form = CheckoutForm()
    if form.validate_on_submit():
        # 再次檢查庫存
        for item in items:
            if item['product'].stock < item['quantity']:
                flash(f'商品 {item["product"].name} 庫存不足，僅剩 {item["product"].stock} 件', 'danger')
                return redirect(url_for('cart'))
        order_number = f"PEG{datetime.now().strftime('%Y%m%d%H%M%S')}{current_user.id}{uuid.uuid4().hex[:4]}"
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
            item['product'].stock -= item['quantity']
        if current_user.is_authenticated:
            CartItem.query.filter_by(user_id=current_user.id).delete()
        else:
            session.pop('cart', None)
        db.session.commit()
        flash(f'訂單已提交，訂單號: {order_number}', 'success')
        return redirect(url_for('order_detail', order_id=order.id))
    if request.method == 'GET':
        form.shipping_name.data = f"{current_user.first_name} {current_user.last_name}".strip() or current_user.username
        form.shipping_phone.data = current_user.phone
        form.shipping_address.data = current_user.address
    return render_template('checkout.html', form=form, cart_items=items, total=total, cart_count=get_cart_count())

@app.route('/orders')
@login_required
def orders():
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', 'all')
    query = Order.query.filter_by(user_id=current_user.id)
    if status != 'all':
        query = query.filter_by(status=status)
    pagination = query.order_by(Order.created_at.desc()).paginate(page=page, per_page=app.config['ORDERS_PER_PAGE'], error_out=False)
    orders = pagination.items
    return render_template('orders.html', orders=orders, pagination=pagination, current_status=status, cart_count=get_cart_count())

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('無權查看此訂單', 'danger')
        return redirect(url_for('orders'))
    return render_template('order_detail.html', order=order, cart_count=get_cart_count())

@app.route('/order/cancel/<int:order_id>', methods=['POST'])
@login_required
def cancel_order(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id:
        return jsonify({'success': False, 'error': '無權限'}), 403
    if order.status != 'pending':
        return jsonify({'success': False, 'error': '訂單狀態不允許取消'}), 400
    for item in order.items:
        product = Product.query.get(item.product_id)
        if product:
            product.stock += item.quantity
    order.status = 'cancelled'
    db.session.commit()
    return jsonify({'success': True})

# ---------- 用戶認證 ----------
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
                flash('賬號已被禁用', 'danger')
                return redirect(url_for('login'))
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            user.login_count += 1
            db.session.commit()
            merge_cart()
            next_page = request.args.get('next')
            flash(f'歡迎回來，{user.username}！', 'success')
            return redirect(next_page or url_for('index'))
        else:
            flash('用戶名或密碼錯誤', 'danger')
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
        flash('注冊成功！歡迎加入飛馬電腦', 'success')
        return redirect(url_for('index'))
    return render_template('register.html', form=form, cart_count=get_cart_count())

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('已退出登錄', 'info')
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
        flash('個人資料已更新', 'success')
        return redirect(url_for('profile'))
    if request.method == 'GET':
        form.first_name.data = current_user.first_name
        form.last_name.data = current_user.last_name
        form.phone.data = current_user.phone
        form.address.data = current_user.address
    recent_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).limit(5).all()
    return render_template('profile.html', form=form, recent_orders=recent_orders, cart_count=get_cart_count())

@app.route('/change-password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    if not current_password or not new_password or not confirm_password:
        flash('請填寫所有密碼字段', 'danger')
        return redirect(url_for('profile'))
    if new_password != confirm_password:
        flash('新密碼與確認密碼不一致', 'danger')
        return redirect(url_for('profile'))
    if len(new_password) < 6:
        flash('新密碼長度至少6位', 'danger')
        return redirect(url_for('profile'))
    if not current_user.check_password(current_password):
        flash('當前密碼錯誤', 'danger')
        return redirect(url_for('profile'))
    current_user.set_password(new_password)
    db.session.commit()
    flash('密碼已更新，請重新登錄', 'success')
    logout_user()
    return redirect(url_for('login'))

# ---------- 商品評價 ----------
@app.route('/product/<int:product_id>/review', methods=['POST'])
@login_required
def add_review(product_id):
    product = Product.query.get_or_404(product_id)
    rating = request.form.get('rating', type=int)
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    if not rating or rating < 1 or rating > 5:
        flash('請選擇評分', 'danger')
        return redirect(url_for('product_detail', slug=product.slug))
    if not content:
        flash('請填寫評價內容', 'danger')
        return redirect(url_for('product_detail', slug=product.slug))
    existing = Review.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        flash('您已經評價過此商品', 'warning')
        return redirect(url_for('product_detail', slug=product.slug))
    review = Review(user_id=current_user.id, product_id=product_id, rating=rating, title=title, content=content, is_active=True)
    db.session.add(review)
    db.session.commit()
    flash('感謝您的評價！', 'success')
    return redirect(url_for('product_detail', slug=product.slug))

# ---------- 收藏功能（可選） ----------
@app.route('/api/wishlist/add', methods=['POST'])
@login_required
def add_to_wishlist():
    data = request.get_json()
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'message': '缺少商品ID'}), 400
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'success': False, 'message': '商品不存在'}), 404
    existing = Wishlist.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing:
        return jsonify({'success': False, 'message': '已收藏過該商品'})
    wish = Wishlist(user_id=current_user.id, product_id=product_id)
    db.session.add(wish)
    db.session.commit()
    return jsonify({'success': True, 'message': '已添加到收藏夾'})

# ---------- API 購物車數量 ----------
@app.route('/api/cart/count')
def api_cart_count():
    return jsonify({'count': get_cart_count()})

# ---------- Session 購物車 API（未登錄用戶）----------
@app.route('/cart/session/update/<int:product_id>', methods=['POST'])
def update_session_cart():
    """更新 session 購物車中商品數量（未登錄用戶）"""
    data = request.get_json()
    quantity = data.get('quantity', 1)
    product_id = data.get('product_id')
    if not product_id:
        return jsonify({'success': False, 'error': '缺少商品ID'}), 400
    
    cart = session.get('cart', {})
    if quantity <= 0:
        cart.pop(str(product_id), None)
    else:
        cart[str(product_id)] = quantity
    session['cart'] = cart
    
    # 重新計算總金額
    items, total = get_cart_items()
    return jsonify({
        'success': True,
        'new_quantity': quantity,
        'cart_total': total,
        'cart_count': sum(item['quantity'] for item in items)
    })

@app.route('/cart/session/remove/<int:product_id>', methods=['POST'])
def remove_session_cart_item(product_id):
    """從 session 購物車刪除商品（未登錄用戶）"""
    cart = session.get('cart', {})
    cart.pop(str(product_id), None)
    session['cart'] = cart
    return jsonify({'success': True})





# ---------- 初始化數據庫和默認數據 ----------
with app.app_context():
    db.create_all()
    if Category.query.count() == 0:
        default_categories = [
            ('cpu', 'CPU處理器', 1),
            ('gpu', '顯卡', 2),
            ('motherboard', '主板', 3),
            ('ram', '內存', 4),
            ('ssd', '固態硬盤', 5),
            ('psu', '電源', 6),
            ('case', '機箱', 7),
            ('cooler', '散熱器', 8),
            ('peripheral', '外設', 9),
        ]
        for slug, name, order in default_categories:
            cat = Category(name=name, slug=slug, sort_order=order, is_active=True)
            db.session.add(cat)
        admin = User(username='admin', email='admin@pegasus.com', first_name='Admin', last_name='User', is_admin=True, is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)