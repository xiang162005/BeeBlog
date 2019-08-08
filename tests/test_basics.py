import unittest
from flask import current_app
from app import create_app, db

class BasicsTestCase(unittest.TestCase):
    # 每个测试启动前运行
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    # 每个测试结束前运行
    def tearDown(self):
        # remove用来清除session
        # 保证每个测试开始时都有一个干净的session
        # 防止前一个测试session.commit()失败或者其他原因留存的session对本次测试的干扰
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 测试应用是否存在
    def test_app_exists(self):
        self.assertFalse(current_app is None)

    # 测试应用是否在测试环境中
    def test_app_is_testing(self):
        self.assertTrue(current_app.config['TESTING'])
