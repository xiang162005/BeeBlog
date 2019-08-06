from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db, login_manager


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    users = db.relationship('User', backref='role')

    def __repr__(self):
        return '<Role {}>'.format(self.name)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, index=True)
    email = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))

    # 把password方法变为属性，读取属性
    @property
    def password(self):
        raise AttributeError('密码属性不可读')

    # 设置密码（设置password属性）
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    # 检查密码
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)    

    def __repr__(self):
        return '<User {}>'.format(self.username) 


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))