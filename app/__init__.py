from flask import Flask
from flask_bootstrap import Bootstrap
from config import configdic


bootstrap = Bootstrap()


# 创建Flask应用
def create_app(config_name):
    app = Flask(__name__)
    # 从config导入配置
    app.config.from_object(configdic[config_name])
    configdic[config_name].init_app(app)

    bootstrap.init_app(app)


    # 添加路由
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)


    return app