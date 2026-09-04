"""
企业员工管理系统后端API
使用Flask框架构建RESTful API
"""
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
from datetime import datetime, timedelta
import logging
import os

from config import config
from models import db, User, Department, Attendance, LeaveRequest, Task, Salary, Announcement

app = Flask(__name__)

env = os.getenv('FLASK_ENV', 'development')
app.config.from_object(config[env])

db.init_app(app)
CORS(app, resources={r"/api/*": {"origins": "*"}})
jwt = JWTManager(app)

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"],
    storage_uri="memory://"
)

os.makedirs('logs', exist_ok=True)
os.makedirs('uploads', exist_ok=True)

logging.basicConfig(
    level=app.config['LOG_LEVEL'],
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(app.config['LOG_FILE']),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def role_required(roles):
    """检查用户角色是否有权限访问"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            current_user = get_jwt_identity()
            if current_user['role'] not in roles:
                return jsonify({'error': '权限不足'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '资源未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f'服务器错误: {error}')
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(429)
def ratelimit_error(error):
    return jsonify({'error': '请求过于频繁，请稍后再试'}), 429

@app.route('/')
def index():
    """返回前端页面"""
    return render_template('index.html')

# ============================================
# 用户认证API
# ============================================

@app.route('/api/auth/register', methods=['POST'])
def register():
    """用户注册接口"""
    try:
        data = request.get_json()
        
        required_fields = ['username', 'email', 'password', 'full_name']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({'error': f'缺少必填字段: {field}'}), 400
        
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'error': '用户名已存在'}), 400
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'error': '邮箱已被注册'}), 400
        
        # 检查是否注册为管理员
        is_admin = data.get('is_admin', False)
        role = 'employee'
        
        if is_admin:
            # 验证管理员密钥
            admin_key = data.get('admin_key', '')
            if admin_key != app.config['ADMIN_SECRET_KEY']:
                return jsonify({'error': '管理员密钥错误'}), 403
            role = 'admin'
        
        user = User(
            username=data['username'],
            email=data['email'],
            full_name=data['full_name'],
            role=role,
            is_admin=(role == 'admin'),
            department=data.get('department')
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        logger.info(f'新用户注册: {user.username}, 角色: {user.role}')
        return jsonify(user.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'注册失败: {str(e)}')
        return jsonify({'error': f'注册失败: {str(e)}'}), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        
        if 'username' not in data or 'password' not in data:
            return jsonify({'error': '请输入用户名和密码'}), 400
        
        user = User.query.filter_by(username=data['username']).first()
        
        if not user or not user.check_password(data['password']):
            return jsonify({'error': '用户名或密码错误'}), 401
        
        if not user.is_active:
            return jsonify({'error': '账号已被禁用'}), 403
        
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(
            identity={
                'user_id': user.user_id,
                'username': user.username,
                'role': user.role,
                'department': user.department,
                'is_admin': user.is_admin
            },
            expires_delta=timedelta(hours=24)
        )
        
        logger.info(f'用户登录: {user.username}')
        return jsonify({
            'access_token': access_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        logger.error(f'登录失败: {str(e)}')
        return jsonify({'error': '登录失败'}), 500

@app.route('/api/auth/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """获取当前登录用户信息"""
    try:
        current_user = get_jwt_identity()
        user = User.query.get(current_user['user_id'])
        
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        logger.error(f'获取当前用户信息失败: {str(e)}')
        return jsonify({'error': '获取当前用户信息失败'}), 500

# ============================================
# 用户管理API
# ============================================

@app.route('/api/users', methods=['GET'])
@jwt_required()
def get_users():
    """获取所有用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)
        
        query = User.query
        pagination = query.paginate(page=page, per_page=per_page, error_out=False)
        
        return jsonify({
            'users': [user.to_dict() for user in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        logger.error(f'获取用户列表失败: {str(e)}')
        return jsonify({'error': '获取用户列表失败'}), 500

@app.route('/api/users/<int:user_id>/department', methods=['PUT'])
@role_required(['admin'])
def assign_department(user_id):
    """分配员工部门（仅管理员）"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '用户不存在'}), 404
        
        data = request.get_json()
        department = data.get('department')
        
        if not department:
            return jsonify({'error': '请提供部门名称'}), 400
        
        user.department = department
        db.session.commit()
        
        logger.info(f'管理员分配部门: 用户{user.username} -> {department}')
        return jsonify(user.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'分配部门失败: {str(e)}')
        return jsonify({'error': f'分配部门失败: {str(e)}'}), 500

# ============================================
# 部门管理API
# ============================================

@app.route('/api/departments', methods=['GET'])
@jwt_required()
def get_departments():
    """获取部门列表"""
    try:
        departments = Department.query.all()
        return jsonify([dept.to_dict() for dept in departments]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/departments', methods=['POST'])
@role_required(['admin'])
def create_department():
    """创建部门"""
    try:
        data = request.get_json()
        
        if not data.get('dept_name'):
            return jsonify({'error': '部门名称不能为空'}), 400
        
        dept = Department(
            dept_name=data['dept_name'],
            description=data.get('description')
        )
        db.session.add(dept)
        db.session.commit()
        
        return jsonify(dept.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/departments/<int:dept_id>', methods=['DELETE'])
@role_required(['admin'])
def delete_department(dept_id):
    """删除部门"""
    try:
        dept = Department.query.get(dept_id)
        if not dept:
            return jsonify({'error': '部门不存在'}), 404
        
        db.session.delete(dept)
        db.session.commit()
        return jsonify({'message': '部门已删除'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# ============================================
# 考勤管理API
# ============================================

@app.route('/api/attendance/check-in', methods=['POST'])
@jwt_required()
def check_in():
    """上班打卡"""
    try:
        current_user = get_jwt_identity()
        user_id = current_user['user_id']
        
        today = datetime.now().date()
        existing = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.check_in) == today
        ).first()
        
        if existing:
            return jsonify({'error': '今天已经打过卡了'}), 400
        
        now = datetime.now()
        attendance = Attendance(
            user_id=user_id,
            check_in=now,
            status='present'
        )
        
        if now.hour >= 9 and now.minute > 0:
            attendance.status = 'late'
            attendance.remark = f'迟到 {now.hour - 9} 小时 {now.minute} 分钟'
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify(attendance.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'打卡失败: {str(e)}'}), 500

@app.route('/api/attendance/check-out', methods=['POST'])
@jwt_required()
def check_out():
    """下班打卡"""
    try:
        current_user = get_jwt_identity()
        user_id = current_user['user_id']
        
        today = datetime.now().date()
        attendance = Attendance.query.filter(
            Attendance.user_id == user_id,
            db.func.date(Attendance.check_in) == today
        ).first()
        
        if not attendance:
            return jsonify({'error': '请先进行上班打卡'}), 400
        
        if attendance.check_out:
            return jsonify({'error': '已经打过下班卡了'}), 400
        
        now = datetime.now()
        attendance.check_out = now
        attendance.work_hours = attendance.calculate_work_hours()
        
        if now.hour >= 18:
            overtime = (now - now.replace(hour=18, minute=0, second=0, microsecond=0)).total_seconds() / 3600
            attendance.overtime_hours = round(overtime, 2)
        
        db.session.commit()
        
        return jsonify(attendance.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'下班打卡失败: {str(e)}'}), 500

@app.route('/api/attendance', methods=['GET'])
@jwt_required()
def get_attendance_records():
    """获取考勤记录列表"""
    try:
        current_user = get_jwt_identity()
        user_id = current_user['user_id']
        
        query = Attendance.query
        
        if current_user['role'] == 'employee':
            query = query.filter_by(user_id=user_id)
        
        query = query.order_by(Attendance.check_in.desc())
        records = query.limit(100).all()
        
        return jsonify({
            'records': [attendance.to_dict() for attendance in records],
            'total': len(records)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取考勤记录失败: {str(e)}'}), 500

# ============================================
# 任务管理API
# ============================================

@app.route('/api/tasks', methods=['GET'])
@jwt_required()
def get_tasks():
    """获取任务列表"""
    try:
        current_user = get_jwt_identity()
        
        query = Task.query
        
        if current_user['role'] == 'employee':
            query = query.filter_by(assigned_to=current_user['user_id'])
        
        tasks = query.order_by(Task.created_at.desc()).all()
        
        return jsonify({
            'tasks': [task.to_dict() for task in tasks],
            'total': len(tasks)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取任务列表失败: {str(e)}'}), 500

@app.route('/api/tasks', methods=['POST'])
@jwt_required()
def create_task():
    """创建任务"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if 'title' not in data:
            return jsonify({'error': '任务标题不能为空'}), 400
        
        due_date = None
        if data.get('due_date'):
            try:
                due_date = datetime.strptime(data['due_date'], '%Y-%m-%d').date()
            except:
                return jsonify({'error': '日期格式错误'}), 400
        
        task = Task(
            title=data['title'],
            description=data.get('description'),
            assigned_to=data.get('assigned_to', current_user['user_id']),
            created_by=current_user['user_id'],
            priority=data.get('priority', 'medium'),
            due_date=due_date
        )
        
        db.session.add(task)
        db.session.commit()
        
        return jsonify(task.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建任务失败: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['PUT'])
@jwt_required()
def update_task(task_id):
    """更新任务"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        data = request.get_json()
        
        if 'title' in data:
            task.title = data['title']
        if 'description' in data:
            task.description = data['description']
        if 'status' in data:
            task.status = data['status']
            if data['status'] == 'done':
                task.completed_at = datetime.utcnow()
        if 'priority' in data:
            task.priority = data['priority']
        if 'assigned_to' in data:
            task.assigned_to = data['assigned_to']
        
        db.session.commit()
        return jsonify(task.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'更新任务失败: {str(e)}'}), 500

@app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
@jwt_required()
def delete_task(task_id):
    """删除任务"""
    try:
        task = Task.query.get(task_id)
        if not task:
            return jsonify({'error': '任务不存在'}), 404
        
        db.session.delete(task)
        db.session.commit()
        return jsonify({'message': '任务已删除'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'删除任务失败: {str(e)}'}), 500

# ============================================
# 请假管理API
# ============================================

@app.route('/api/leave-requests', methods=['POST'])
@jwt_required()
def create_leave_request():
    """创建请假申请"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if 'leave_type' not in data or 'start_date' not in data or 'end_date' not in data:
            return jsonify({'error': '缺少必填字段'}), 400
        
        try:
            start_date = datetime.strptime(data['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(data['end_date'], '%Y-%m-%d').date()
        except:
            return jsonify({'error': '日期格式错误'}), 400
        
        if end_date < start_date:
            return jsonify({'error': '结束日期不能早于开始日期'}), 400
        
        leave = LeaveRequest(
            user_id=current_user['user_id'],
            leave_type=data['leave_type'],
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason', '')
        )
        
        db.session.add(leave)
        db.session.commit()
        
        return jsonify(leave.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'创建请假申请失败: {str(e)}'}), 500

@app.route('/api/leave-requests', methods=['GET'])
@jwt_required()
def get_leave_requests():
    """获取请假申请列表"""
    try:
        current_user = get_jwt_identity()
        user_id = current_user['user_id']
        
        query = LeaveRequest.query
        
        if current_user['role'] == 'employee':
            query = query.filter_by(user_id=user_id)
        
        query = query.order_by(LeaveRequest.created_at.desc())
        leaves = query.limit(100).all()
        
        return jsonify({
            'records': [leave.to_dict() for leave in leaves],
            'total': len(leaves)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取请假申请失败: {str(e)}'}), 500

# 在 app.py 的请假管理API部分添加以下路由

@app.route('/api/leave-requests/<int:leave_id>/approve', methods=['PUT'])
@role_required(['admin', 'manager'])
def approve_leave(leave_id):
    """审批请假申请"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        leave = LeaveRequest.query.get(leave_id)
        if not leave:
            return jsonify({'error': '请假申请不存在'}), 404
        
        new_status = data.get('status', 'approved')
        if new_status not in ['approved', 'rejected']:
            return jsonify({'error': '无效的审批状态'}), 400
        
        leave.status = new_status
        leave.approved_by = current_user['user_id']
        leave.approved_at = datetime.utcnow()
        
        db.session.commit()
        
        logger.info(f'用户 {current_user["user_id"]} 审批请假 {leave_id}: {new_status}')
        return jsonify(leave.to_dict()), 200
        
    except Exception as e:
        db.session.rollback()
        logger.error(f'审批请假失败: {str(e)}')
        return jsonify({'error': f'审批请假失败: {str(e)}'}), 500

# ============================================
# 公告管理API
# ============================================

@app.route('/api/announcements', methods=['GET'])
@jwt_required()
def get_announcements():
    """获取公告列表"""
    try:
        announcements = Announcement.query.order_by(Announcement.created_at.desc()).all()
        
        return jsonify({
            'announcements': [announcement.to_dict() for announcement in announcements],
            'total': len(announcements)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'获取公告失败: {str(e)}'}), 500

@app.route('/api/announcements', methods=['POST'])
@role_required(['admin', 'manager'])
def create_announcement():
    """发布公告"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        if 'title' not in data or 'content' not in data:
            return jsonify({'error': '缺少必填字段'}), 400
        
        announcement = Announcement(
            title=data['title'],
            content=data['content'],
            posted_by=current_user['user_id'],
            priority=data.get('priority', 'normal')
        )
        
        db.session.add(announcement)
        db.session.commit()
        
        return jsonify(announcement.to_dict()), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'发布公告失败: {str(e)}'}), 500

# ============================================
# 健康检查
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """系统健康检查"""
    try:
        db.session.execute('SELECT 1')
        db_status = 'healthy'
    except Exception as e:
        db_status = f'unhealthy: {str(e)}'
    
    return jsonify({
        'status': 'running',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat()
    }), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin = User(
                username='admin',
                email='admin@company.com',
                full_name='系统管理员',
                role='admin',
                is_admin=True,
                department='技术部'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print('默认管理员账号创建成功: admin/admin123')
    
    app.run(host='0.0.0.0', port=5000, debug=True)