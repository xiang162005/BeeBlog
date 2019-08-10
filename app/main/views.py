from flask import render_template, redirect, url_for, flash
from flask_login import login_required
from . import main
from .forms import EditProfileAdminForm
from ..models import User
from ..decorators import admin_required

# 网站主页
@main.route('/')
def index():
    return render_template('index.html')


# 个人主页
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user)


# 管理员编辑用户个人资料界面
@main.route('/editprofile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        user.session.add(user)
        user.session.commit()
        flash('用户的个人资料已更新')
        return redirect(url_for('main.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('auth/edit_profile.html', form=form, user=user)