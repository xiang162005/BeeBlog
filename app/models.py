import bleach
import os
from datetime import datetime
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from markdown import markdown
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from . import db, login_manager


# 用户权限定义
class Permission:
    # 关注用户
    FOLLOW = 1
    # 发表评论
    COMMENT = 2
    # 写文章
    WRITE = 4
    # 管理他人发表的评论
    MODERATE = 8
    # 管理网站
    ADMIN = 16
    # 点赞文章
    LIKE = 32

# 角色表
class Role(db.Model):
    __tablename__ = 'roles'
    # 角色ID（主键）
    id = db.Column(db.Integer, primary_key=True)
    # 角色名称
    name = db.Column(db.String(64), unique=True)
    # 每个角色包含哪些用户
    users = db.relationship('User', backref='role', lazy='dynamic')
    # 是否为默认角色，只有默认角色为True，其余均为False
    default = db.Column(db.Boolean, default=False, index=True)
    # 角色权限
    permissions = db.Column(db.Integer)

    def __init__(self, **kwargs):
        super(Role, self).__init__(**kwargs)
        if self.permissions is None:
            self.permissions = 0

    # 获得权限
    def add_permission(self, perm):
        if not self.has_permission(perm):
            self.permissions += perm

    # 删除权限
    def remove_permission(self, perm):
        if self.has_permission(perm):
            self.permissions -= perm

    # 重置权限
    def reset_permissions(self):
        self.permissions = 0

    # 检查是否有此项权限
    def has_permission(self, perm):
        return (self.permissions & perm) == perm

    # 赋予角色相应权限
    @staticmethod
    def insert_roles():
        # 定义各角色权限的字典
        roles_dic = {
            # 普通用户：具有关注、评论、写文章的权限
            'User': [Permission.FOLLOW, Permission.COMMENT, Permission.WRITE, Permission.LIKE],
            # 协管员：具有关注、评论、写文章、管理评论的权限
            'Moderator': [Permission.FOLLOW, Permission.COMMENT,
                          Permission.WRITE, Permission.MODERATE, Permission.LIKE],
            # 管理员：具有关注、评论、写文章、管理评论、管理网站的权限
            'Administrator': [Permission.FOLLOW, Permission.COMMENT,
                              Permission.WRITE, Permission.MODERATE,
                              Permission.ADMIN, Permission.LIKE]
        }
        # 默认角色为普通用户
        default_role = 'User'
        # 生成角色权限
        for r in roles_dic:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            for perm in roles_dic[r]:
                role.add_permission(perm)
            role.default = (role.name==default_role)
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role {}>'.format(self.name)


# 关注与被关注 关联表
class Follow(db.Model):
    __tablename__ = 'follows'
    # 关注者id
    follower_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    # 被关注者id
    followed_id = db.Column(db.Integer, db.ForeignKey('users.id'),
                            primary_key=True)
    # 关注时间
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)



# 用户表
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    # 用户ID（主键）
    id = db.Column(db.Integer, primary_key=True)
    # 用户名
    username = db.Column(db.String(64), unique=True, index=True)
    # 邮箱
    email = db.Column(db.String(64), unique=True, index=True)
    # 用户角色ID（外键）
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    # 用户密码hash值
    password_hash = db.Column(db.String(128))
    # 确认注册状态
    confirmed = db.Column(db.Boolean, default=False)
    # 用户昵称
    name = db.Column(db.String(64))
    # 用户地址
    location = db.Column(db.String(64))
    # 个人简介
    about_me = db.Column(db.Text())
    # 注册时间
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    # 上次登陆时间
    last_login = db.Column(db.DateTime(), default=datetime.utcnow)
    # 用户大头像路径
    b_avatar = db.Column(db.String(128), default='default/big.jpg')
    # 用户小头像路径
    s_avatar = db.Column(db.String(128), default='default/small.jpg')
    # 用户发表的文章
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    # 我的粉丝（关注我的人）
    follower = db.relationship('Follow',
                                foreign_keys=[Follow.followed_id],
                                backref=db.backref('followed', lazy='joined'),
                                lazy='dynamic',
                                # 启动所有层叠选项，删除孤儿记录
                                cascade='all, delete-orphan')
    # 我关注的人
    followed = db.relationship('Follow',
                               foreign_keys=[Follow.follower_id],
                               backref=db.backref('follower', lazy='joined'),
                               lazy='dynamic',
                               # 启动所有层叠选项，删除孤儿记录
                               cascade='all, delete-orphan')
    # 评论
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    # 阅读过的文章
    viewed_posts = db.relationship('View', backref='viewer', lazy='dynamic')
    # 点赞过的文章
    liked_posts = db.relationship('PostLike', backref='liker', lazy='dynamic')

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['MAIL_ADMIN']:
                self.role = Role.query.filter_by(name='Administrator').first()
            else:
                self.role = Role.query.filter_by(default=True).first()

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

    # 生成注册token
    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    # 确认注册
    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        db.session.commit()
        return True
    
    # 生成重设密码token
    def generate_reset_password_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'reset_password': self.id}).decode('utf-8')

    # 确认重设密码
    @staticmethod
    def confirm_reset_password(token, new_password):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        user = User.query.get(data.get('reset_password'))
        if user is None:
            return False
        user.password = new_password
        db.session.add(user)
        db.session.commit()
        return True

    # 生成修改邮箱地址token
    def generate_change_email_token(self, new_email, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'change_email': self.id, 'new_email': new_email}).decode('utf-8')

    # 确认修改邮箱地址
    def change_email(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('change_email') != self.id:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if User.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email  
        db.session.add(self)
        db.session.commit()
        return True

    # 检查用户是否有某项权限
    def can(self, perm):
        return self.role is not None and self.role.has_permission(perm)

    # 检查用户是否为管理员
    def is_administrator(self):
        return self.can(Permission.ADMIN)

    # 更新上次登陆时间
    def update_last_login(self):
        self.last_login = datetime.utcnow()
        db.session.add(self)
        db.session.commit()

    # 关注用户
    def follow(self, user):
        if not self.is_following(user):
            f = Follow(follower=self, followed=user)
            db.session.add(f)

    # 取消关注用户
    def unfollow(self, user):
        f = self.followed.filter_by(followed_id=user.id).first()
        if f:
            db.session.delete(f)

    # 我是否关注了用户
    def is_following(self, user):
        if user.id is None:
            return False
        return self.followed.filter_by(
            followed_id=user.id).first() is not None

    # 用户是否关注了我
    def is_followed_by(self, user):
        if user.id is None:
            return False
        return self.followers.filter_by(
            follower_id=user.id).first() is not None

    # 我关注的用户所写的文章
    @property
    def followed_posts(self):
        return Post.query.join(Follow, Follow.followed_id == Post.author_id)\
            .filter(Follow.follower_id == self.id)

    # 用户是否阅读过该文章
    def is_viewed(self, post_id):
        view = self.viewed_posts.filter_by(post_id=post_id).first()
        if view:
            return True
        return False

    # 用户是否点赞过该文章
    def is_post_liked(self, post_id):
        like = self.liked_posts.filter_by(post_id=post_id).first()
        if like:
            return True
        return False

    # 点赞文章
    def post_like(self, id):
        if not self.is_post_liked(id):
            like = PostLike(post_id=id, liker_id=self.id)
            db.session.add(like)

    # 取消关注用户
    def post_unlike(self, id):
        unlike = self.liked_posts.filter_by(post_id=id).first()   
        if unlike:
            db.session.delete(unlike)

    def __repr__(self):
        return '<User {}>'.format(self.username) 

# 匿名用户类
# 与Users类的两个方法相同，
# 方便应用直接检查权限，无须区分用户是否登陆，便可直接检查权限
class AnonymousUser(AnonymousUserMixin):
    # 检查匿名用户是否有某项权限
    def can(self, perm):
        return False

    # 检查匿名用户是否为管理员
    def is_administrator(self):
        return False
       

# 匿名用户为AnonymousUser类
login_manager.anonymous_user = AnonymousUser


# 文章表
class Post(db.Model):
    __tablename__ = 'posts'
    # 文章id（主键）
    id = db.Column(db.Integer, primary_key=True)
    # 文章标题
    title = db.Column(db.String(64))
    # 文章主体
    body = db.Column(db.Text)
    # 文章主体html
    body_html = db.Column(db.Text)
    # 文章摘要
    abstract = db.Column(db.String(64))
    # 创建时间
    ctime = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    # 作者id（外键）
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    # 评论
    comments = db.relationship('Comment', backref='post', lazy='dynamic')
    # 阅读者
    views = db.relationship('View', backref='post', lazy='dynamic')
    # 点赞者
    likes = db.relationship('PostLike', backref='post', lazy='dynamic')

    # 把Markdown文本转化成html
    @staticmethod
    # target, value, oldvalue, initiator均由db.event.listen的set参数自行传人
    def on_change_body(target, value, oldvalue, initiator):
        # 允许存在的html标签
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        # 把Markdown文本转换为html
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))

# 监听程序，Post.body有改动就运行Post.on_change_body
db.event.listen(Post.body, 'set', Post.on_change_body)


# 文章阅读者表
class View(db.Model):
    __tablename__ = 'views'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    viewer_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# 文章点赞表
class PostLike(db.Model):
    __tablename__ = 'post_likes'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))
    liker_id = db.Column(db.Integer, db.ForeignKey('users.id'))


# 评论表
class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    disabled = db.Column(db.Boolean)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    post_id = db.Column(db.Integer, db.ForeignKey('posts.id'))

    @staticmethod
    def on_change_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'code', 'em', 'i',
                         'strong']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True))


# 监听程序，Comment.body有改动就运行Comment.on_change_body
db.event.listen(Comment.body, 'set', Comment.on_change_body)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))