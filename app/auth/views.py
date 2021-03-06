import os
from flask import render_template, redirect, request, url_for, flash, \
    current_app
from flask_login import current_user, login_user, logout_user, login_required
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm, \
    ResetPasswordRequestForm, ResetPasswordForm, ChangeEmailRequestForm, \
    EditProfileForm    
from .. import db
from ..models import User
from ..email import send_email
from ..image import create_avatar


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        # 更新用户上次登陆时间
        current_user.update_last_login()
        # 如果用户还未确认注册信息，则跳转到未确认注册界面
        if not current_user.confirmed \
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



# 修改密码
@auth.route('/changepassword', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.oldpassword.data):
            current_user.password=form.newpassword.data
            db.session.add(current_user)
            db.session.commit()
            flash('成功修改密码')
            return redirect(url_for('main.index'))
        flash('原密码错误，修改密码失败')
    return render_template('auth/changepassword.html', form=form)


# 请求重设密码
@auth.route('/resetpasswordrequest', methods=['GET', 'POST'])
def reset_password_request():
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_password_token()
            send_email(user.email, '重设密码',
                       'auth/email/reset_password',
                       user=user, token=token)
            flash('一封重设密码的电子邮件已经发送至您的邮箱，请登陆邮箱确认')
            return redirect(url_for('auth.login'))
        flash('此邮箱还未注册，请先注册')
    return render_template('auth/reset_password.html', form=form)


# 重设密码
@auth.route('/resetpassword/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if not current_user.is_anonymous:
        return redirect(url_for('main.index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        if User.confirm_reset_password(token, form.newpassword.data):
            flash('成功重设密码')
            return redirect(url_for('auth.login'))
        else:
            flash('重设密码验证失败，请重新申请')
            return redirect(url_for('auth.reset_password_request'))
    return render_template('auth/reset_password.html', form=form)


# 请求修改邮箱
@auth.route('/changeemailrequest', methods=['GET', 'POST'])
@login_required
def change_email_request():
    form = ChangeEmailRequestForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.password.data):
            token = current_user.generate_change_email_token(form.newemail.data)
            send_email(form.newemail.data, '修改邮箱地址',
                       'auth/email/change_email',
                       user=current_user, token=token)
            flash('一封确认新邮箱信息的电子邮件已发送至您的新邮箱，请登陆新邮箱确认')
            return redirect(url_for('main.index'))
        flash('密码错误，修改邮箱地址失败')
    return render_template('auth/change_email.html', form=form)


# 修改邮箱
@auth.route('/changeemail/<token>')
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash('您的邮箱地址已更改，请重新登陆')
        return redirect(url_for('auth.login'))
    flash('修改邮箱验证失败，请重新申请')
    return redirect(url_for('main.index'))


# 编辑个人资料
@auth.route('/editprofile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        # 提交用户头像
        avatar = request.files['avatar']
        if avatar:
            if not create_avatar(avatar):
                flash('文件类型错误')
                return redirect(url_for('main.user', username=current_user.username))
        db.session.add(current_user)
        db.session.commit()
        flash('您的个人资料已更新，如头像未更新，请刷新浏览器以显示新的头像')
        return redirect(url_for('main.user', username=current_user.username))
    form.avatar.data = os.path.join(current_app.config['AVATAR_DEST'], current_user.b_avatar)
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('auth/edit_profile.html', form=form, user=current_user)