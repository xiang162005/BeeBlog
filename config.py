# 基础环境配置
class Config:
    @staticmethod
    def init_app(app):
        pass


# 开发环境配置
class DevelopmentConfig(Config):
    DEBUG = True


# 测试环境配置
class TestingConfig(Config):
    TESTING = True


# 生产环境配置
class ProductionConfig(Config):
    pass


# 配置字典
configdic = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    # 默认环境为开发环境
    'default': DevelopmentConfig
}