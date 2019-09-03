import os
from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import Role, User


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


# 配置shell命令字典
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


# 配置单元测试命令
@app.cli.command()
def test():
    """启动单元测试"""
    import unittest
    # 创建测试套件并从tests文件夹查找所有测试模块
    tests = unittest.TestLoader().discover('tests')
    # run()运行tests里的所有测试并将结果打印到stdout
    # verbosity=2是指测试结果的输出的详细程度，有0-6级
    unittest.TextTestRunner(verbosity=2).run(tests)


# 配置部署命令
@app.cli.command()
def deploy():
    """Run deployment tasks."""
    # 把数据库迁移到最新修订版本
    upgrade()

    # 创建或更新用户角色
    Role.insert_roles()