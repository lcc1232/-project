from flask import Flask,render_template,request,redirect,url_for,flash,session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import hashlib  #加密
from functools import wraps

# Flask	            创建 Flask 应用实例的核心类
# render_template	渲染 HTML 模板文件，返回给浏览器
# request	        获取客户端发送的请求数据（如表单、JSON、查询参数）
# redirect	        重定向用户到另一个 URL
# url_for	        根据路由函数名反向生成 URL（例如 url_for('index') → /）
# flash	            在请求之间传递一次性消息（如错误提示），配合模板中的 get_flashed_messages() 使用
# SQLAlchemy	    ORM（对象关系映射）工具，让我们用 Python 类操作数据库，而不是写 SQL
# datetime	        Python 标准库，用于处理日期和时间
# wraps	            装饰器工具，保留被装饰函数的元信息
# hashlib	        密码加密（SHA256 哈希算法）

app=Flask(__name__)

# Flask(__name__)	创建 Flask 实例，__name__ 告诉 Flask 模板文件夹位置

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///blog.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY']='dev_key_123'

# SQLALCHEMY_DATABASE_URI	        数据库连接地址。sqlite:///blog.db 表示使用 SQLite 数据库，文件名为 blog.db，会在项目根目录自动创建
# SQLALCHEMY_TRACK_MODIFICATIONS	设为 False 关闭对象修改追踪，节省内存和性能（Flask-SQLAlchemy 官方推荐）
# SECRET_KEY	                    密钥，用于保护 session 和 flash 消息，生产中要换成复杂且保密的字符串

db=SQLAlchemy(app)  #初始化数据库

# 创建 db 对象，它是操作数据库的入口。app 传入后，Flask 和 SQLAlchemy 就绑定在一起了。


class Article(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    title=db.Column(db.String(100),nullable=False)
    content=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime,default=datetime.now)
    views=db.Column(db.Integer,default=0)  #点击量

    user_id=db.Column(db.Integer,db.ForeignKey('user.id'),nullable=False)  #作者ID,关联到User表
    #user_id 是"外键"，指向 User 表的 id。这样每篇文章都知道是谁写的。


# db.Model：所有模型类的基类，继承后 Article 就成为一个数据库表

# id	        Integer	            整数类型，primary_key=True 设为主键
# title	        String(100)	        字符串，最大长度 100，nullable=False 表示不能为空
# content	    Text	            长文本类型，适合存储文章正文
# created_at	DateTime	        日期时间类型，default=datetime.now 在创建记录时自动填入当前时间
# views =	                        定义一个新的列，列名叫做 views
# db.Column	                        告诉 SQLAlchemy 这是一个数据库列
# db.Integer	                    列的数据类型是整数
# default=0	                        默认值是 0，新创建的文章初始点击量为 0

class User(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(50),unique=True,nullable=False)
    password=db.Column(db.String(200),nullable=False)
    is_admin=db.Column(db.Boolean,default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)  #注册时间，自动生成

    #db.relationship('Article')：       告诉 SQLAlchemy，User 和 Article 有关联
    # backref='author'：                在 Article 中自动创建 author 属性，可以通过 article.author 获取作者
    # lazy=True：                       访问 user.articles 时才查询数据库（延迟加载）
    articles = db.relationship('Article', backref='author', lazy=True)

# unique=True： 用户名不能重复，防止两个人注册同一个名字
# password      长度设为 200，因为加密后的密码会变长
# is_admin      默认 False，普通人注册都是普通用户


# 创建数据库
with app.app_context():
    db.create_all()

# app.app_context() 创建 Flask 应用上下文，让代码可以访问应用配置
# db.create_all() 扫描所有继承 db.Model 的类，在数据库中创建对应的表
# 如果表已存在，不会重复创建


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# password.encode()	    把字符串转成字节（SHA256 需要字节输入）
# hashlib.sha256()	    创建 SHA256 哈希对象
# .hexdigest()	        返回十六进制字符串（长度 64

# sha256 是一种加密算法，把明文密码变成一串看不懂的字符。
# 比如 "123456" 加密后变成 "8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92"


def get_current_user():
    user_id = session.get('user_id')
    if user_id:
        return User.query.get(user_id)
    return None

# session.get('user_id')	    从 session 中获取当前登录用户的 ID
# User.query.get(user_id)	    根据 ID 查询用户对象
# 返回 None	                    如果没有登录，返回 None

# 使用场景：在需要用户信息的地方调用，避免重复写查询代码。


def login_required(f):
    """要求用户必须登录才能访问"""
    @wraps(f)  #保留原函数的名称和文档字符串（调试用）
    def decorated_function(*args,**kwargs):
        if 'user_id' not in session:  #检查是否登录
            flash("请先登录！",'warning')  #显示提示信息
            return redirect(url_for('login'))  #重定向，跳转到登录页面
        return f(*args,**kwargs)
    return decorated_function

# 这个装饰器就像一个"门卫"，放在路由前面。如果用户没登录，就把他挡回去并跳转到登录页。

def edit_required(funct):
    def decorated_funct(*args,**kwargs):
        if 'article.author.username'!=session.username:
            flash('登录账户不是文章作者！','warning')
            return redirect(url_for('post'))
        return funct(*args,**kwargs)
    return decorated_funct

# 路由：首页
@app.route("/")
def index():
    articles=Article.query.order_by(Article.created_at.desc()).all()

    top_articles=Article.query.order_by(Article.views.desc()).limit(10).all()  #排行榜，取前十

# Article.query	                        开始查询 Article 表
# .order_by(Article.views.desc())	    按 views（点击量）降序排列，数字大的排前面
# .limit(10)	                        只取前 10 条记录
# .all()	                            执行查询，返回结果列表

    return render_template('index.html',articles=articles,top_articles=top_articles)

# @app.route('/')	                                    装饰器，将函数绑定到根路径 /，用户访问首页时触发
# Article.query	                                        对 Article 表的查询入口
# .order_by(Article.created_at.desc())	                按创建时间降序排列（最新文章在前）
# .all()	                                            执行查询，返回所有匹配的记录列表
# render_template('index.html', articles=articles)	    渲染模板，并将 articles 数据传给 HTML，在模板中可以用 articles 变量遍历

# 路由：文章详情
@app.route("/post/<int:article_id>")
def post(article_id):
    article=Article.query.get_or_404(article_id)

    article.views+=1  #每次访问，点击量+1（Python 的增强赋值语法）
    db.session.commit()  #提交事务，把修改保存到数据库中。没有这行，点击量不会真正写入数据库

    top_articles = Article.query.order_by(Article.views.desc()).limit(10).all()
    return render_template('post.html',article=article,top_articles=top_articles)

# '/post/<int:article_id>'	                        URL 路径中带变量，例如 /post/3，article_id 会被解析为整数
# Article.query.get_or_404(article_id)	            根据主键查询记录，如果不存在自动返回 404 页面
# render_template('post.html', article=article)	    渲染详情页模板，把查询到的文章对象传过去

# 路由：发布文章
@app.route("/create",methods=['GET','POST'])
@login_required
def create():
    if request.method=='POST':
        title=request.form.get('title','').strip()
        content=request.form.get('content','').strip()

        if not title or not content:
            flash('标题和内容不能为空!','danger')
        else:
            #创建文章时，关联当前登录的用户
            new_article=Article(
                title=title,
                content=content,
                user_id=session['user_id']  #从session获取当前用户ID
                )
            db.session.add(new_article)
            db.session.commit()
            return redirect(url_for('index'))
        
    top_articles = Article.query.order_by(Article.views.desc()).limit(10).all()
    return render_template('create.html',top_articles=top_articles)

# 请求流程：

# GET 请求（用户访问 /create）：
# 直接渲染 create.html，显示空表单

# POST 请求（用户提交表单）：
# request.form['title'] 从表单中获取标题
# request.form['content'] 从表单中获取内容
# 如果标题或内容为空 → 用 flash() 存储错误消息，重新渲染表单
# 如果都填了 → 创建 Article 对象，添加到数据库会话（db.session.add），提交事务（db.session.commit），最后重定向到首页

#路由：编辑文章
@app.route('/edit/<int:article_id>',methods=['GET','POST'])
@login_required
def edit(article_id):
    article=Article.query.get_or_404(article_id)  #根据ID查询文章

    if article.user_id!=session['user_id']:
        flash('你不是原文作者！','danger')
        return redirect(url_for('post',article_id=article_id))

    if request.method=='POST':  #用户提交了表单
        title=request.form['title']  #获取新标题
        content=request.form['content']  #获取新内容

        if not title or not content:
            flash('标题和内容不能为空！','danger')

        

        else:
            article.title=title  #把新标题赋给文章对象
            article.content=content  #把新内容赋给文章对象
            db.session.commit()  #提交事务，保存到数据库
            flash('文章更新成功！','success')
            return redirect(url_for('post',article_id=article_id))

    #GET请求：显示编辑表单
    top_articles = Article.query.order_by(Article.views.desc()).limit(10).all()
    return render_template('edit.html',article=article,top_articles=top_articles)

# @app.route('/edit/<int:article_id>', methods=['GET', 'POST'])	    同一个 URL 支持两种请求方式
# article = Article.query.get_or_404(article_id)	                查询要编辑的文章，不存在就返回 404
# request.method == 'POST'	                                        判断用户是提交表单（POST）还是访问页面（GET）
# request.form['title']	                                            从表单中获取用户输入的标题
# article.title = title	                                            把文章对象的标题属性更新为新值
# db.session.commit()	                                            关键：提交事务，把修改保存到数据库
# redirect(url_for('post', article_id=article.id))	                更新完成后跳转到文章详情页

#路由：删除文章
@app.route('/delete/<int:article_id>',methods=['POST'])
@login_required
def delete(article_id):
    article=Article.query.get_or_404(article_id)  #查询要删除的文章
    db.session.delete(article)  #标记文章对象为“待删除”
    if article.user_id!=session['user_id']:
        flash('你不是原文作者！','danger')
        return redirect(url_for('post',article_id=article_id))
    db.session.commit()         #提交事务，真正删除
    flash('文章已删除！','success')
    return redirect(url_for('index'))  #重定向到首页

#路由：注册
@app.route('/register',methods=["GET","POST"])
def register():
    if request.method=='POST':

        #1.获取用户提交的数据
        username=request.form.get('username','').strip()
        password=request.form.get('password','').strip()

        #2.验证：用户名和密码不为空
        if not username or not password:
            flash("用户和密码不能为空！",'danger')
            return render_template('register.html')

        #3.检查用户名是否被占用
        existing_user=User.query.filter_by(username=username).first()
        if existing_user:
            flash("用户名已被占用，请换一个！","danger")
            return render_template('register.html')

        #4.加密密码
        hashed_password=hash_password(password)

        #5.创建新用户
        new_user=User(
            username=username,
            password=hashed_password,
            is_admin=False  #默认普通用户
        )

        #6.保存到数据库
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功！请登录。','success')
        return redirect(url_for('login'))  #跳转到登录页

    #GET 请求：显示注册单
    return render_template('register.html')

# @app.route('/register', methods=['GET', 'POST'])	    这个 URL 支持两种请求：GET（显示表单）和 POST（提交表单）
# request.method == 'POST'	                            判断用户是不是在提交表单
# request.form.get('username', '').strip()	            从表单获取用户名，如果没有则返回空字符串，并去掉首尾空格
# User.query.filter_by(username=username).first()	    在数据库中查找是否有同名用户
# hash_password(password)	                            把明文密码加密
# db.session.add(new_user)	                            把新用户添加到数据库会话
# db.session.commit()	                                真正保存到数据库
# flash('注册成功！', 'success')	                     显示一条一次性消息
# redirect(url_for('login'))	                        跳转到登录页面

#路由：登录
@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":

        #1.获取用户输入的数据
        username=request.form.get('username','').strip()
        password=request.form.get('password','').strip()

        #2.验证不能为空
        if not username or not password:
            flash("用户名和密码不能为空！",'danger')
            return render_template('login')

        #3.在数据库中查找用户
        user=User.query.filter_by(username=username).first()

        #4.验证密码
        if user and user.password==hash_password(password):
            #登陆成功：保存用户信息到session
            session['user_id']=user.id          #int
            session['username']=user.username   #string
            session['is_admin']=user.is_admin   #boolean

            flash(f"欢迎回来，{user.username}!",'success')
            return redirect(url_for('index'))

        else:
            #登陆失败
            flash("用户名或密码错误！",'danger')

    #GET请求：显示登录表单
    return render_template("login.html")

# session['user_id'] = user.id	                            把用户 ID 存到 session，用于判断用户是否登录
# session['username'] = user.username	                    存用户名，方便在导航栏显示
# session['is_admin'] = user.is_admin	                    存管理员状态（以后扩展用）
# if user and user.password == hash_password(password)	    用户存在且密码匹配

#路由：登出
@app.route('/logout')
def logout():
    """用户退出登录"""
    session.clear()  # 清除所有 session 数据
    flash('已退出登录！', 'info')
    return redirect(url_for('index'))

# session.clear() 会清空所有保存的用户信息，用户就变成"未登录"状态了。

if __name__=='__main__':
    app.run(debug=True)