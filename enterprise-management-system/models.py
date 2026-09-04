"""
数据库模型定义
使用SQLAlchemy ORM定义所有数据表结构
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from flask import current_app

# 创建SQLAlchemy实例
db = SQLAlchemy()

class User(db.Model):
    """用户模型类，对应users表"""
    __tablename__ = 'users'
    
    # 定义表字段
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='employee')  # admin/manager/employee
    department = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    avatar_url = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # 新增字段
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # 定义关系
    attendances = db.relationship('Attendance', backref='user', lazy='dynamic')
    leave_requests = db.relationship('LeaveRequest', backref='applicant', lazy='dynamic', 
                                    foreign_keys='LeaveRequest.user_id')
    tasks = db.relationship('Task', backref='assignee', lazy='dynamic',
                           foreign_keys='Task.assigned_to')
    
    def set_password(self, password):
        """设置密码，使用bcrypt加密"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """验证密码是否正确"""
        return check_password_hash(self.password_hash, password)
    
    def generate_token(self, expires_in=3600):
        """生成JWT令牌"""
        payload = {
            'user_id': self.user_id,
            'username': self.username,
            'role': self.role,
            'is_admin': self.is_admin,
            'exp': datetime.utcnow().timestamp() + expires_in
        }
        return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
    
    @staticmethod
    def verify_token(token):
        """验证JWT令牌"""
        try:
            payload = jwt.decode(token, current_app.config['JWT_SECRET_KEY'], 
                               algorithms=['HS256'])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    def to_dict(self):
        """将用户对象转换为字典"""
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'department': self.department,
            'phone': self.phone,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }

class Department(db.Model):
    """部门模型类"""
    __tablename__ = 'departments'
    
    dept_id = db.Column(db.Integer, primary_key=True)
    dept_name = db.Column(db.String(100), unique=True, nullable=False)
    parent_dept_id = db.Column(db.Integer, db.ForeignKey('departments.dept_id'))
    manager_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    parent_dept = db.relationship('Department', remote_side=[dept_id], backref='sub_departments')
    manager = db.relationship('User', backref='managed_departments')
    
    def to_dict(self):
        return {
            'dept_id': self.dept_id,
            'dept_name': self.dept_name,
            'parent_dept_id': self.parent_dept_id,
            'manager_id': self.manager_id,
            'description': self.description,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Attendance(db.Model):
    """考勤记录模型类"""
    __tablename__ = 'attendance'
    
    attendance_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    check_in = db.Column(db.DateTime, nullable=False)
    check_out = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='present')
    overtime_hours = db.Column(db.Float, default=0)
    work_hours = db.Column(db.Float)
    remark = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_work_hours(self):
        """计算工作时长"""
        if self.check_out and self.check_in:
            diff = self.check_out - self.check_in
            hours = diff.total_seconds() / 3600
            return max(0, round(hours - 1, 2))
        return 0
    
    def to_dict(self):
        return {
            'attendance_id': self.attendance_id,
            'user_id': self.user_id,
            'check_in': self.check_in.isoformat() if self.check_in else None,
            'check_out': self.check_out.isoformat() if self.check_out else None,
            'status': self.status,
            'overtime_hours': float(self.overtime_hours) if self.overtime_hours else 0,
            'work_hours': float(self.work_hours) if self.work_hours else 0,
            'remark': self.remark,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class LeaveRequest(db.Model):
    """请假申请模型类"""
    __tablename__ = 'leave_requests'
    
    leave_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    leave_type = db.Column(db.String(20), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text)
    status = db.Column(db.String(20), default='pending')
    approved_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    approved_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    approver = db.relationship('User', foreign_keys=[approved_by], backref='approved_leaves')
    
    def to_dict(self):
        return {
            'leave_id': self.leave_id,
            'user_id': self.user_id,
            'leave_type': self.leave_type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'reason': self.reason,
            'status': self.status,
            'approved_by': self.approved_by,
            'approved_at': self.approved_at.isoformat() if self.approved_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Task(db.Model):
    """任务模型类"""
    __tablename__ = 'tasks'
    
    task_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    created_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    project_id = db.Column(db.Integer)
    priority = db.Column(db.String(10), default='medium')
    status = db.Column(db.String(20), default='todo')
    due_date = db.Column(db.Date)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_tasks')
    
    def to_dict(self):
        return {
            'task_id': self.task_id,
            'title': self.title,
            'description': self.description,
            'assigned_to': self.assigned_to,
            'created_by': self.created_by,
            'project_id': self.project_id,
            'priority': self.priority,
            'status': self.status,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Salary(db.Model):
    """薪资模型类"""
    __tablename__ = 'salaries'
    
    salary_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    base_salary = db.Column(db.Float, nullable=False)
    bonus = db.Column(db.Float, default=0)
    allowance = db.Column(db.Float, default=0)
    insurance = db.Column(db.Float, default=0)
    tax = db.Column(db.Float, default=0)
    net_salary = db.Column(db.Float)
    salary_month = db.Column(db.Date, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_net_salary(self):
        """计算实发工资"""
        net = float(self.base_salary) + float(self.bonus) + float(self.allowance) - \
              float(self.insurance) - float(self.tax)
        return round(net, 2)
    
    def to_dict(self):
        return {
            'salary_id': self.salary_id,
            'user_id': self.user_id,
            'base_salary': float(self.base_salary),
            'bonus': float(self.bonus),
            'allowance': float(self.allowance),
            'insurance': float(self.insurance),
            'tax': float(self.tax),
            'net_salary': float(self.net_salary) if self.net_salary else None,
            'salary_month': self.salary_month.isoformat() if self.salary_month else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class Announcement(db.Model):
    """公告模型类"""
    __tablename__ = 'announcements'
    
    announcement_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    posted_by = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    priority = db.Column(db.String(10), default='normal')
    expires_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    poster = db.relationship('User', backref='announcements')
    
    def to_dict(self):
        return {
            'announcement_id': self.announcement_id,
            'title': self.title,
            'content': self.content,
            'posted_by': self.posted_by,
            'priority': self.priority,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }