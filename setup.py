import os
from flask_migrate import Migrate
from app import create_app, db
from app.models import Role, User


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
migrate = Migrate(app, db)


# 配置shell命令字典
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


# 配置单元测试命令
pass

