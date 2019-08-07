from flask import render_template, redirect, request, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from . import auth
from .forms import LoginForm, RegistrationForm
from .. import db
from ..models import User
from ..email import send_email


@auth.before_app_request
def before_request():
    if current_user.is_authenticated \
            and not current_user.confirmed \
            and request.blueprint != 'auth' \
            and request.endpoint != 'static':
        return redirect(url_for('auth.unconfirmed'))


# 登陆
@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            # 用户访问未授权的URL时，会把原URL写入next,并跳到登陆界面
            # 如果是访问登陆界面，由于此界面无需授权，所以next为None
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                next = url_for('main.index')
            return redirect(next)
        flash('邮箱或密码错误')
    return render_template('auth/login.html', form=form)


# 登出
@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('成功退出登陆')
    return redirect(url_for('main.index'))


# 注册
@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, '确认注册信息',
                   'auth/email/confirm', user=user, token=token)
        flash('一封确认注册信息的电子邮件已发送至您的注册邮箱，请登陆邮箱确认')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


# 确认注册信息邮件
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('成功确认注册信息，您的账户已被激活')
    else:
        flash('确认注册信息失败')
    return redirect(url_for('main.index'))


# 未确认注册信息
@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html')


# 重新发送确认注册信息的邮件
@auth.route('/reconfirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, '确认注册信息', 
               'auth/email/confirm', user=current_user, token=token)
    flash('一封新的确认注册信息的电子邮件已发送至您的注册邮箱，请登陆邮箱确认')
    return redirect(url_for('main.index'))



