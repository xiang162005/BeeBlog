import os


# 基础环境配置
class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    # 邮件服务器主机名或IP地址
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.126.com')
    # 邮件服务器端口
    MAIL_PORT = int(os.environ.get('MAIL_PORT', '465'))
    # 启用SSL
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', '1']
    # 邮件账户的用户名
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    # 邮件账户的密码
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    # 邮件主题前缀
    MAIL_SUBJECT_PREFIX = '[蜜蜂博客]'
    # 邮件发件人
    MAIL_SENDER = '蜜蜂博客(BeeBlog)<beeblog@126.com>'
    # 邮件收件人（管理员邮箱）
    MAIL_ADMIN = os.environ.get('MAIL_ADMIN')
    # 禁止数据库自动提交
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # 上传头像路径
    AVATAR_DEST = os.path.abspath(os.path.join(os.getcwd(),"app/static/avatar"))
    # 上传头像类型限制
    ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif']
    # 每页显示的文章数量
    POSTS_PER_PAGE = 10
    # 每页显示的粉丝数量
    FOLLOWERS_PER_PAGE = 20
    # 每页显示的评论数量
    COMMENTS_PER_PAGE = 10

    @staticmethod
    def init_app(app):
        pass


# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URI')


# 测试环境配置
class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URI')


# 生产环境配置
class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URI')
    # 应用出错时发送电子邮件
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)

        # 出错时邮件通知管理员
        import logging
        from logging.handlers import SMTPHandler
        credentials = None
        secure = None
        if getattr(cls, 'MAIL_USERNAME', None) is not None:
            credentials = (cls.MAIL_USERNAME, cls.MAIL_PASSWORD)
            if getattr(cls, 'MAIL_USE_SSL', None):
                secure = ()
        mail_handler = SMTPHandler(
            mailhost=(cls.MAIL_SERVER, cls.MAIL_PORT),
            fromaddr=cls.MAIL_SENDER,
            toaddrs=[cls.MAIL_ADMIN],
            subject=cls.MAIL_SUBJECT_PREFIX + '程序错误',
            credentials=credentials,
            secure=secure)
        mail_handler.setLevel(logging.ERROR)
        app.logger.addHandler(mail_handler)
    


# 配置字典
configdic = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    # 默认环境为开发环境
    'default': DevelopmentConfig
}

