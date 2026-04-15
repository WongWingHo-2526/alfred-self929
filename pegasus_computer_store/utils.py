# utils.py - 工具函數模塊
import os
import uuid
import re
from datetime import datetime
from functools import wraps
from flask import session, current_app, url_for
from flask_login import current_user
from werkzeug.utils import secure_filename
from models import db, Product, CartItem, User

# ---------- 購物車輔助函數 ----------
def get_cart_count():
    """獲取當前購物車中的商品總數"""
    if current_user.is_authenticated:
        return CartItem.query.filter_by(user_id=current_user.id).count()
    else:
        cart = session.get('cart', {})
        return sum(cart.values())

def get_cart_items():
    """
    獲取購物車中的商品詳情和總金額
    返回: (items_list, total_price)
    items_list 中每個元素包含: id, product, quantity, subtotal
    """
    items = []
    total = 0.0
    
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
    """用戶登錄時，將 session 購物車合並到數據庫"""
    if current_user.is_authenticated:
        session_cart = session.pop('cart', {})
        for product_id, quantity in session_cart.items():
            product_id = int(product_id)
            cart_item = CartItem.query.filter_by(
                user_id=current_user.id, 
                product_id=product_id
            ).first()
            if cart_item:
                cart_item.quantity += quantity
            else:
                cart_item = CartItem(
                    user_id=current_user.id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
        db.session.commit()

def clear_cart():
    """清空當前用戶的購物車"""
    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session.pop('cart', None)

# ---------- 文件上傳輔助函數 ----------
def allowed_file(filename):
    """檢查文件擴展名是否允許上傳"""
    if not filename:
        return False
    allowed_extensions = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, subfolder=''):
    """
    保存上傳的文件，返回保存的文件名（唯一）
    :param file: Flask 上傳文件對象
    :param subfolder: 子文件夾名（可選）
    :return: 保存的文件名（不含路徑），失敗返回 None
    """
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename):
        return None
    
    filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_folder = os.path.join(upload_folder, subfolder)
        os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, unique_filename)
    file.save(filepath)
    return unique_filename

def delete_uploaded_file(filename, subfolder=''):
    """刪除上傳的文件"""
    if not filename:
        return
    upload_folder = current_app.config['UPLOAD_FOLDER']
    if subfolder:
        upload_folder = os.path.join(upload_folder, subfolder)
    filepath = os.path.join(upload_folder, filename)
    if os.path.exists(filepath):
        os.remove(filepath)

# ---------- 訂單號生成 ----------
def generate_order_number(user_id):
    """
    生成唯一訂單號
    格式: PEG + 年月日時分秒 + 用戶ID + 4位隨機字符
    """
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_suffix = uuid.uuid4().hex[:4].upper()
    return f"PEG{timestamp}{user_id}{random_suffix}"

# ---------- 郵件發送（可選，需要配置） ----------
def send_email(recipient, subject, body, html=None):
    """
    發送郵件（需要配置郵件服務器）
    使用前需安裝 flask-mail 並配置
    """
    try:
        from flask_mail import Mail, Message
        mail = Mail(current_app)
        msg = Message(subject, recipients=[recipient])
        msg.body = body
        if html:
            msg.html = html
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"郵件發送失敗: {e}")
        return False

def send_verification_email(user):
    """發送郵箱驗證郵件"""
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(user.email, salt='email-verify')
    verify_url = url_for('verify_email', token=token, _external=True)
    subject = "飛馬電腦 - 郵箱驗證"
    body = f"請點擊以下鏈接驗證您的郵箱：\n{verify_url}\n\n鏈接24小時內有效。"
    return send_email(user.email, subject, body)

def send_password_reset_email(user):
    """發送密碼重置郵件"""
    from itsdangerous import URLSafeTimedSerializer
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(user.email, salt='password-reset')
    reset_url = url_for('reset_password', token=token, _external=True)
    subject = "飛馬電腦 - 密碼重置"
    body = f"請點擊以下鏈接重置密碼：\n{reset_url}\n\n鏈接24小時內有效。"
    return send_email(user.email, subject, body)

# ---------- 數據驗證輔助函數 ----------
def validate_phone(phone):
    """驗證香港手機號碼格式（簡單示例）"""
    if not phone:
        return True
    # 香港手機: 5,6,9 開頭，8位數字
    pattern = r'^[569]\d{7}$'
    return bool(re.match(pattern, phone))

def validate_email(email):
    """驗證郵箱格式"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def validate_password_strength(password):
    """
    密碼強度驗證
    返回 (is_valid, message)
    """
    if len(password) < 6:
        return False, "密碼長度至少6位"
    if len(password) > 50:
        return False, "密碼長度不能超過50位"
    # 可選：要求包含數字和字母
    # if not re.search(r'[0-9]', password) or not re.search(r'[A-Za-z]', password):
    #     return False, "密碼需包含字母和數字"
    return True, ""

# ---------- 分頁輔助 ----------
def paginate(query, page, per_page, error_out=False):
    """簡化的分頁函數"""
    return query.paginate(page=page, per_page=per_page, error_out=error_out)

# ---------- 裝飾器 ----------
def admin_required(f):
    """管理員權限裝飾器（備用，實際在 admin.py 中已有）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            flash('需要管理員權限', 'danger')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# ---------- 日志記錄（可選） ----------
def log_action(user_id, action, details=None):
    """
    記錄用戶操作日志（需要創建 Log 模型）
    此處僅作示例
    """
    # 如需實現，可創建 Log 模型並在此處添加記錄
    pass