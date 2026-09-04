"""
初始化测试数据脚本
创建50个员工、100个任务、3个公告、5个请假申请
"""
from app import app, db
from models import User, Department, Attendance, LeaveRequest, Task, Salary, Announcement
from datetime import datetime, timedelta
import random

def init_test_data():
    """初始化测试数据"""
    with app.app_context():
        # 清空现有数据（可选）
        print("清空现有数据...")
        db.drop_all()
        db.create_all()
        
        # 创建部门
        print("创建部门...")
        departments = [
            Department(dept_name='技术部', description='负责技术研发'),
            Department(dept_name='市场部', description='负责市场推广'),
            Department(dept_name='人事部', description='负责招聘和人事管理'),
            Department(dept_name='财务部', description='负责财务管理'),
            Department(dept_name='销售部', description='负责销售业务'),
            Department(dept_name='客服部', description='负责客户服务')
        ]
        db.session.add_all(departments)
        db.session.commit()
        
        # 创建管理员
        print("创建管理员...")
        admin = User(
            username='admin',
            email='admin@company.com',
            full_name='系统管理员',
            role='admin',
            department='技术部',
            phone='13800000001'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        
        # 创建50个员工
        print("创建50个员工...")
        first_names = ['张', '李', '王', '刘', '陈', '杨', '赵', '黄', '周', '吴',
                      '徐', '孙', '马', '朱', '胡', '郭', '何', '高', '林', '罗',
                      '郑', '梁', '谢', '宋', '唐', '许', '韩', '冯', '邓', '曹',
                      '彭', '曾', '肖', '田', '董', '袁', '潘', '蒋', '蔡', '余',
                      '杜', '叶', '程', '苏', '魏', '吕', '丁', '任', '沈', '姚']
        last_names = ['伟', '芳', '娜', '敏', '静', '丽', '强', '磊', '军', '洋',
                     '勇', '艳', '杰', '娟', '涛', '明', '超', '秀兰', '霞', '平']
        
        employees = []
        dept_names = ['技术部', '市场部', '人事部', '财务部', '销售部', '客服部']
        
        for i in range(50):
            username = f'employee{i+1:03d}'
            email = f'employee{i+1:03d}@company.com'
            full_name = f'{random.choice(first_names)}{random.choice(last_names)}'
            dept = random.choice(dept_names)
            
            # 每5个员工中有一个经理
            role = 'manager' if (i + 1) % 10 == 0 else 'employee'
            
            employee = User(
                username=username,
                email=email,
                full_name=full_name,
                role=role,
                department=dept,
                phone=f'138{random.randint(10000000, 99999999)}'
            )
            employee.set_password('123456')
            employees.append(employee)
        
        db.session.add_all(employees)
        db.session.commit()
        print(f"✓ 创建了50个员工")
        
        # 创建100个任务
        print("创建100个任务...")
        tasks = []
        task_titles = [
            '完成项目需求分析', '开发用户登录功能', '优化数据库查询', '编写API文档',
            '修复系统Bug', '实现数据导出功能', '设计用户界面', '测试系统性能',
            '部署生产环境', '编写单元测试', '优化前端性能', '实现缓存机制',
            '开发报表功能', '集成第三方服务', '重构代码结构', '实现消息推送',
            '开发移动端适配', '优化搜索引擎', '实现权限管理', '开发通知系统'
        ]
        task_descriptions = [
            '详细分析项目需求并编写文档',
            '实现用户登录认证功能',
            '优化数据库查询性能',
            '编写完整的API接口文档',
            '修复系统中存在的Bug',
            '实现数据导出为Excel功能',
            '设计现代化的用户界面',
            '进行系统性能测试',
            '部署应用到生产环境',
            '编写完整的单元测试',
            '优化前端页面加载速度',
            '实现Redis缓存机制',
            '开发数据报表功能',
            '集成第三方支付服务',
            '重构现有代码结构',
            '实现实时消息推送',
            '开发移动端响应式设计',
            '优化SEO搜索引擎',
            '实现细粒度权限管理',
            '开发系统通知功能'
        ]
        
        priorities = ['low', 'medium', 'high', 'urgent']
        statuses = ['todo', 'in_progress', 'review', 'done']
        
        for i in range(100):
            task = Task(
                title=f'{random.choice(task_titles)} - {i+1}',
                description=random.choice(task_descriptions),
                assigned_to=random.choice(employees).user_id,
                created_by=admin.user_id,
                priority=random.choice(priorities),
                status=random.choice(statuses),
                due_date=datetime.now().date() + timedelta(days=random.randint(1, 30))
            )
            tasks.append(task)
        
        db.session.add_all(tasks)
        db.session.commit()
        print(f"✓ 创建了100个任务")
        
        # 创建3个公告
        print("创建公告...")
        announcements = [
            Announcement(
                title='公司年度总结大会通知',
                content='各位同事：公司将于本周五下午2点在会议室召开年度总结大会，请准时参加。',
                posted_by=admin.user_id,
                priority='important'
            ),
            Announcement(
                title='系统升级通知',
                content='系统将于本周六凌晨2点进行升级维护，届时系统将暂停服务2小时。',
                posted_by=admin.user_id,
                priority='urgent'
            ),
            Announcement(
                title='新员工入职培训',
                content='下周一将举行新员工入职培训，请相关部门做好准备。',
                posted_by=admin.user_id,
                priority='normal'
            )
        ]
        db.session.add_all(announcements)
        db.session.commit()
        print(f"✓ 创建了3个公告")
        
        # 创建5个请假申请
        print("创建请假申请...")
        leave_types = ['annual', 'sick', 'personal', 'other']
        leave_reasons = [
            '需要休息调整',
            '身体不适需要就医',
            '家中有事需要处理',
            '参加重要活动',
            '个人事务'
        ]
        
        leaves = []
        for i in range(5):
            start_date = datetime.now().date() + timedelta(days=random.randint(1, 10))
            end_date = start_date + timedelta(days=random.randint(1, 3))
            leave = LeaveRequest(
                user_id=random.choice(employees[:20]).user_id,  # 前20个员工
                leave_type=random.choice(leave_types),
                start_date=start_date,
                end_date=end_date,
                reason=random.choice(leave_reasons),
                status='pending'
            )
            leaves.append(leave)
        
        db.session.add_all(leaves)
        db.session.commit()
        print(f"✓ 创建了5个请假申请")
        
        # 创建一些考勤记录
        print("创建考勤记录...")
        attendances = []
        for emp in employees[:10]:  # 为前10个员工创建考勤
            for day in range(5):  # 最近5天
                check_in_time = datetime.now().replace(hour=9, minute=random.randint(0, 30)) - timedelta(days=day)
                check_out_time = check_in_time + timedelta(hours=8, minutes=random.randint(0, 30))
                attendance = Attendance(
                    user_id=emp.user_id,
                    check_in=check_in_time,
                    check_out=check_out_time,
                    status='present' if check_in_time.hour <= 9 else 'late',
                    work_hours=8.5
                )
                attendances.append(attendance)
        
        db.session.add_all(attendances)
        db.session.commit()
        print(f"✓ 创建了考勤记录")
        
        print("\n" + "="*50)
        print("数据初始化完成！")
        print("="*50)
        print(f"管理员: admin / admin123")
        print(f"员工账号: employee001 ~ employee050 / 123456")
        print(f"经理账号: employee010, employee020, employee030, employee040, employee050")
        print("="*50)

if __name__ == '__main__':
    init_test_data()