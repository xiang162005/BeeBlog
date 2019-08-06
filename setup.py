import os
from app import create_app


app = create_app(os.getenv('FLASK_CONFIG') or 'default')


# 配置shell命令字典
@app.shell_context_processor
def make_shell_context():
    return dict()


# 配置单元测试命令
pass

