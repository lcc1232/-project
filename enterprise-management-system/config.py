"""
系统配置文件
包含数据库连接、JWT密钥、加密配置等
"""
import os
from datetime import timedelta
from dotenv import load_dotenv

# 加载环境变量文件
load_dotenv()

class Config:
    """基础配置类"""
    
    # 数据库配置 - 使用PostgreSQL
    DB_HOST = os.getenv('DB_HOST', 'localhost')        # 数据库主机地址
    DB_PORT = os.getenv('DB_PORT', '5433')             # 数据库端口
    DB_NAME = os.getenv('DB_NAME', 'enterprise_management')  # 数据库名称
    DB_USER = os.getenv('DB_USER', 'postgres')         # 数据库用户名
    DB_PASSWORD = os.getenv('DB_PASSWORD', '123456') # 数据库密码
    
    # 构建SQLAlchemy数据库连接URI
    # 使用psycopg2驱动连接PostgreSQL
    SQLALCHEMY_DATABASE_URI = f'postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # 关闭修改跟踪以提高性能
    
    # JWT配置 - 用于身份验证
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this')  # JWT密钥
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)      # 访问令牌过期时间：1小时
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)     # 刷新令牌过期时间：30天
    
    # 密码加密配置
    BCRYPT_LOG_ROUNDS = 12  # bcrypt加密轮数，越高越安全但越慢

    ADMIN_SECRET_KEY = 'EMS2024Admin@#$'
    
    # CORS配置 - 允许跨域请求
    CORS_ORIGINS = ['*']  # 允许的前端地址
    
    # 文件上传配置
    UPLOAD_FOLDER = 'uploads'                          # 上传文件存储目录
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024              # 最大上传文件大小：16MB
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx'}  # 允许的文件类型
    
    # 邮件配置 - 用于发送通知
    MAIL_SERVER = os.getenv('MAIL_SERVER', 'smtp.gmail.com')  # 邮件服务器
    MAIL_PORT = int(os.getenv('MAIL_PORT', 587))       # 邮件端口
    MAIL_USE_TLS = True                                # 使用TLS加密
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')         # 邮件用户名
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')         # 邮件密码
    
    # Redis配置 - 用于缓存和会话管理
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # 日志配置
    LOG_LEVEL = 'INFO'                                 # 日志级别
    LOG_FILE = 'logs/app.log'                          # 日志文件路径

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True                                       # 开启调试模式
    SQLALCHEMY_ECHO = True                             # 打印SQL语句

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False                                      # 关闭调试模式
    SQLALCHEMY_ECHO = False                            # 不打印SQL语句
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=30)    # 生产环境缩短令牌有效期
    
# 配置字典，根据环境选择不同的配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}