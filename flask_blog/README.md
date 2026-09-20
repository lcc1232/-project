# 个人博客系统

基于 Flask + SQLAlchemy + SQLite 开发的个人博客系统，支持用户注册登录、文章发布与管理、点击量统计、热门排行榜等功能。

## 功能

- 用户注册 / 登录 / 登出
- 文章发布、编辑、删除（仅作者可操作自己的文章）
- 文章列表展示与详情查看
- 点击量统计与热门文章排行榜（TOP 10）
- 响应式布局

## 技术栈

- **后端**：Python 3.10、Flask、Flask-SQLAlchemy
- **数据库**：SQLite
- **前端**：Jinja2、Tailwind CSS

## 快速开始

```bash
# 1. 克隆项目
git clone https://github.com/你的用户名/你的仓库名.git
cd 你的仓库名

# 2. 安装依赖
pip install flask flask-sqlalchemy

# 3. 启动应用
python app.py

访问 http://127.0.0.1:5000
