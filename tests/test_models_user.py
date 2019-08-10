import unittest
import time
from app import create_app, db
from app.models import User, Role, Permission, AnonymousUser


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

    # 测试密码存在
    def test_set_password(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        self.assertTrue(user.password_hash is not None)

    # 测试密码不可读
    def test_no_get_password(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        with self.assertRaises(AttributeError):
            user.password

    # 测试验证密码函数
    def test_verify_password(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        self.assertTrue(user.verify_password('cat'))
        self.assertFalse(user.verify_password('dog'))

    # 测试相同密码加密值不同
    def test_password_salts_are_different(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='tom@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        user1 = User.query.filter_by(email='john@example.com').first()
        user2 = User.query.filter_by(email='tom@example.com').first()
        self.assertTrue(user1.password_hash != user2.password_hash)

    # 测试确认注册功能中，有效token会验证成功
    def test_valid_confirmation_token(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token()
        self.assertTrue(user.confirm(token))

    # 测试确认注册功能中，无效token会验证失败
    def test_invalid_confirmation_token(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='tom@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        user1 = User.query.filter_by(email='john@example.com').first()
        user2 = User.query.filter_by(email='tom@example.com').first()
        token = user1.generate_confirmation_token()
        self.assertFalse(user2.confirm(token))

    # 测试确认注册功能中，时间过期会验证失败
    def test_expired_confirmation_token(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_confirmation_token(1)
        time.sleep(2)
        self.assertFalse(user.confirm(token))

    # 测试重设密码功能中，有效token能成功重设密码
    def test_valid_confirm_reset_password(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_reset_password_token()
        self.assertTrue(User.confirm_reset_password(token, 'dog'))
        self.assertTrue(user.verify_password('dog'))

    # 测试重设密码功能中，无效token不能成功重设密码
    def test_invalid_confirm_reset_password(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_reset_password_token()
        self.assertFalse(User.confirm_reset_password(token + '1', 'dog'))
        self.assertFalse(user.verify_password('dog'))
        self.assertTrue(user.verify_password('cat'))

    # 测试重设密码功能中，时间过期不能成功重设密码
    def test_expired_confirm_reset_password(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_reset_password_token(1)
        time.sleep(2)
        self.assertFalse(User.confirm_reset_password(token, 'dog'))
        self.assertFalse(user.verify_password('dog'))
        self.assertTrue(user.verify_password('cat'))

    # 测试重设邮箱功能中，有效token能成功重设邮箱
    def test_valid_change_email(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_change_email_token('tom@example.com')
        self.assertTrue(user.change_email(token))
        self.assertEqual(user.email, 'tom@example.com')
        
    # 测试重设邮箱功能中，无效token不能成功重设邮箱
    def test_invalid_change_email(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='tom@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        user1 = User.query.filter_by(email='john@example.com').first()
        user2 = User.query.filter_by(email='tom@example.com').first()
        token = user1.generate_change_email_token('tony@example.com')
        self.assertFalse(user2.change_email(token))
        self.assertEqual(user2.email, 'tom@example.com')

    # 测试重设邮箱功能中，把邮箱重设为已存在的邮箱会导致失败
    def test_exist_change_email(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='tom@example.com', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        user1 = User.query.filter_by(email='john@example.com').first()
        user2 = User.query.filter_by(email='tom@example.com').first()
        token = user2.generate_change_email_token('john@example.com')
        self.assertFalse(user2.change_email(token))
        self.assertEqual(user2.email, 'tom@example.com')

    # 测试重设邮箱功能中，时间过期不能成功重设邮箱
    def test_expired_change_email(self):
        u = User(email='john@example.com', password='cat')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        token = user.generate_change_email_token('tom@example.com', 1)
        time.sleep(2)
        self.assertFalse(user.change_email(token))
        self.assertEqual(user.email, 'john@example.com')
    
    # 测试普通用户权限
    def test_user_permission(self):
        Role.insert_roles()
        u = User(email='john@example.com')
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertFalse(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))

    # 测试协管员权限
    def test_moderator_permission(self):
        Role.insert_roles()
        r = Role.query.filter_by(name='Moderator').first()
        u = User(email='john@example.com', role=r)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertTrue(user.can(Permission.MODERATE))
        self.assertFalse(user.can(Permission.ADMIN))

    # 测试管理员权限
    def test_administrator_permission(self):
        Role.insert_roles()
        r = Role.query.filter_by(name='Administrator').first()
        u = User(email='john@example.com', role=r)
        db.session.add(u)
        db.session.commit()
        user = User.query.filter_by(email='john@example.com').first()
        self.assertTrue(user.can(Permission.FOLLOW))
        self.assertTrue(user.can(Permission.COMMENT))
        self.assertTrue(user.can(Permission.WRITE))
        self.assertTrue(user.can(Permission.MODERATE))
        self.assertTrue(user.can(Permission.ADMIN))

    # 测试匿名用户权限
    def test_anonymoususer_permission(self):
        Role.insert_roles()
        u = AnonymousUser()
        self.assertFalse(u.can(Permission.FOLLOW))
        self.assertFalse(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.WRITE))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))