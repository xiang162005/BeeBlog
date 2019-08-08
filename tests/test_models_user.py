import unittest
import time
from app import create_app, db
from app.models import User


class UserModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 检查密码存在
    def test_set_password(self):
        u = User(password='cat')
        self.assertTrue(u.password_hash is not None)

    # 检查密码不可读
    def test_no_get_password(self):
        u = User(password='cat')
        with self.assertRaises(AttributeError):
            u.password

    # 检查验证密码函数
    def test_verify_password(self):
        u = User(password='cat')
        self.assertTrue(u.verify_password('cat'))
        self.assertFalse(u.verify_password('dog'))

    # 检查相同密码加密值不同
    def test_password_salts_are_different(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        self.assertTrue(u1.password_hash != u2.password_hash)

    # 检查确认注册功能中，有效token会验证成功
    def test_valid_confirmation_token(self):
        u = User(password='cat')
        # 前几个测试不用提交session，而这个测试需要提交session的原因是：
        # 本测试的confirm方法需要用到self.id, 而不提交就不会有self.id
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    # 检查确认注册功能中，无效token会验证失败
    def test_invalid_confirmation_token(self):
        u1 = User(password='cat')
        u2 = User(password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_confirmation_token()
        self.assertFalse(u2.confirm(token))

    # 检查确认注册功能中，时间过期会验证失败
    def test_expired_confirmation_token(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(u.confirm(token))

    # 检查重设密码功能中，有效token能成功重设密码
    def test_valid_confirm_reset_password(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_password_token()
        self.assertTrue(User.confirm_reset_password(token, 'dog'))
        self.assertTrue(u.verify_password('dog'))

    # 检查重设密码功能中，无效token不能成功重设密码
    def test_invalid_confirm_reset_password(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_password_token()
        self.assertFalse(User.confirm_reset_password(token + '1', 'dog'))
        self.assertFalse(u.verify_password('dog'))
        self.assertTrue(u.verify_password('cat'))

    # 检查重设密码功能中，时间过期不能成功重设密码
    def test_expired_confirm_reset_password(self):
        u = User(password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_reset_password_token(1)
        time.sleep(2)
        self.assertFalse(User.confirm_reset_password(token, 'dog'))
        self.assertFalse(u.verify_password('dog'))
        self.assertTrue(u.verify_password('cat'))

    # 检查重设邮箱功能中，有效token能成功重设邮箱
    def test_valid_change_email(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_change_email_token('tom@example.com')
        self.assertTrue(u.change_email(token))
        self.assertEqual(u.email, 'tom@example.com')
        
    # 检查重设邮箱功能中，无效token不能成功重设邮箱
    def test_invalid_change_email(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='tom@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u1.generate_change_email_token('tony@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertEqual(u2.email, 'tom@example.com')

    # 检查重设邮箱功能中，把邮箱重设为已存在的邮箱会导致失败
    def test_exist_change_email(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='tom@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_change_email_token('john@example.com')
        self.assertFalse(u2.change_email(token))
        self.assertEqual(u2.email, 'tom@example.com')

    # 检查重设邮箱功能中，时间过期不能成功重设邮箱
    def test_expired_change_email(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        token = u.generate_change_email_token('tom@example.com', 1)
        time.sleep(2)
        self.assertFalse(u.change_email(token))
        self.assertEqual(u.email, 'john@example.com')
    