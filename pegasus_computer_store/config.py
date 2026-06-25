import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'pegasus-computer-store-secret-key-change-in-production')
    
    # ─── AWS RDS MYSQL MOUNTING ───────────────────────────────────────────────
    db_host = os.environ.get('DB_HOST')
    db_name = os.environ.get('DB_NAME')
    db_user = os.environ.get('DB_USER')
    db_pass = os.environ.get('DB_PASSWORD')

    if db_host and db_user and db_pass and db_name:
        # Clean trailing ports from the AWS endpoint string if present
        clean_host = db_host.split(':')[0]
        # Assemble the cloud connection URI string using PyMySQL
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{db_user}:{db_pass}@{clean_host}/{db_name}"
    else:
        # Development fallback option
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///pegasus.db')
    # ──────────────────────────────────────────────────────────────────────────

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Session配置
    SESSION_COOKIE_NAME = 'pegasus_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = False  # 開發環境設為False
    
    # 上傳文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    # 分頁配置
    PRODUCTS_PER_PAGE = 12
    ORDERS_PER_PAGE = 10