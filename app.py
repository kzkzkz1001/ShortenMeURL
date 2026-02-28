
import string
import random
from flask import Flask, request, redirect, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
import os
import redis

import logging
import sys

# 1. 初始化 Flask 应用
app = Flask(__name__)

# --- (新) 日志配置 ---
# 配置日志记录器
logging.basicConfig(
    stream=sys.stdout,  # 将日志输出到标准输出 (您的终端)
    level=logging.INFO,  # 日志级别
    format="%(asctime)s [%(levelname)s] [%(name)s] - %(message)s"
)
app.logger = logging.getLogger('ShortenMeLogger')
# -----------------------------

# --- 数据库配置 (无变化) ---
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Zkz20031001@127.0.0.1/url_shortener_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- (新) Redis 缓存配置 ---
try:
    # 'decode_responses=True' 确保我们从 Redis 获取的是字符串，而不是字节(bytes)
    cache = redis.StrictRedis(
        host='localhost', port=6379, db=0, decode_responses=True)
    cache.ping()  # 测试连接
    print("成功连接到 Redis 缓存。")
except Exception as e:
    print(f"警告：无法连接到 Redis。缓存将被禁用。错误：{e}")
    cache = None
# -----------------------------

# --- 数据库模型 (无变化) ---


class URLMap(db.Model):
    __tablename__ = 'url_map'
    id = db.Column(db.Integer, primary_key=True)
    short_code = db.Column(db.String(6), unique=True,
                           nullable=False, index=True)
    long_url = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"<URLMap {self.short_code} -> {self.long_url[:50]}>"

# --- 短代码生成器 (无变化) ---


def generate_short_code(length=6):
    chars = string.ascii_letters + string.digits
    while True:
        code = ''.join(random.choices(chars, k=length))
        exists = URLMap.query.filter_by(short_code=code).first()
        if not exists:
            break
    return code

# --- (新) 中间件：请求日志 ---


@app.before_request
def log_request_info():
    """在每个请求之前记录日志，实现“请求日志”功能 。"""
    app.logger.info(
        f"Incoming Request: {request.method} {request.path} from {request.remote_addr}"
    )
# -----------------------------


# --- (新) 中间件：错误恢复 (404) ---
@app.errorhandler(404)
def handle_not_found(error):
    """
    当 .first_or_404() 失败或路由未找到时，捕获 404 错误。
    返回统一的 JSON 错误响应，而不是 Flask 默认的 HTML 页面 。
    """
    app.logger.warning(f"404 Not Found: {request.path}")
    return jsonify({
        "error": "Not Found",
        "message": "您请求的资源未找到。"
    }), 404
# -----------------------------


# --- (新) 中间件：错误恢复 (400) ---
@app.errorhandler(400)
def handle_bad_request(error):
    """
    当 abort(400, ...) 被调用时（例如 JSON 格式错误），捕获 400 错误 。
    """
    app.logger.warning(f"400 Bad Request: {error.description}")
    return jsonify({
        "error": "Bad Request",
        "message": error.description  # 使用我们从 abort() 传入的消息
    }), 400
# -----------------------------


# --- (新) 中间件：通用错误恢复 (500) ---
@app.errorhandler(Exception)
def handle_generic_error(error):
    """
    捕获所有其他未处理的异常 (例如数据库连接失败)。
    这能提高“系统稳定性” 。
    """
    app.logger.error(f"500 Internal Server Error: {error}", exc_info=True)
    return jsonify({
        "error": "Internal Server Error",
        "message": "服务器发生内部错误。"
    }), 500
# -----------------------------

# --- API Endpoints ---

# (修改) 创建短网址的 API


@app.route('/api/shorten', methods=['POST'])
def shorten_url():
    if not request.json or 'long_url' not in request.json:
        abort(400, description="请求体必须是包含 'long_url' 的 JSON。")

    long_url = request.json['long_url']
    short_code = generate_short_code()

    try:
        new_url_entry = URLMap(short_code=short_code, long_url=long_url)
        db.session.add(new_url_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": f"Database error: {e}"}), 500

    # --- (新) 写入缓存 ---
    if cache:
        try:
            # 设置一个过期时间，例如 1 小时 (3600 秒)
            cache.set(short_code, long_url, ex=3600)
        except Exception as e:
            print(f"警告：写入 Redis 缓存失败。错误：{e}")
    # -----------------------------

    short_url = request.host_url + short_code

    return jsonify({
        "short_url": short_url,
        "long_url": long_url
    }), 201

# (重大修改) 重定向 API


@app.route('/<short_code>', methods=['GET'])
def redirect_to_url(short_code):
    """
    根据 short_code 查找长网址并执行重定向。
    优先从 Redis 缓存中查找。
    """

    # --- (新) 1. 检查缓存 ---
    cached_url = None
    if cache:
        try:
            cached_url = cache.get(short_code)
        except Exception as e:
            print(f"警告：从 Redis 缓存读取失败。错误：{e}")

    if cached_url:
        # 缓存命中 (Hit)！
        print(f"缓存命中: {short_code}")  # (用于调试)
        return redirect(cached_url, code=302)
    # -----------------------------

    # --- (新) 2. 缓存未命中 (Miss) ---
    print(f"缓存未命中: {short_code}")  # (用于调试)

    # 从数据库中查找
    url_entry = URLMap.query.filter_by(short_code=short_code).first_or_404()

    # --- (新) 3. 将结果存入缓存 ---
    if cache:
        try:
            # 将数据库中的值存入缓存，以便下次使用
            cache.set(short_code, url_entry.long_url, ex=3600)
        except Exception as e:
            print(f"警告：写入 Redis 缓存失败。错误：{e}")
    # -----------------------------

    return redirect(url_entry.long_url, code=302)


# --- 运行应用 (无变化) ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
