import os
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash, \
    current_app
from flask_login import current_user, login_required
from . import main
from .forms import EditProfileAdminForm, PostForm
from .. import db
from ..models import User, Permission, Post
from ..decorators import admin_required

# 网站主页
@main.route('/')
def index():
    # 当前页数，默认为1
    page = request.args.get('page', 1, type=int)
    # 每页的文章，per_page为每页显示的文章数量
    # error_out为False时，当请求页数超出范围时，返回空列表
    # error_out为True时，当请求页数超出范围时，返回404
    pagination = Post.query.order_by(Post.ctime.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('index.html', posts=posts, pagination=pagination)


# 个人主页
@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first_or_404()
    # 用户头像的修改时间
    mtime = str(os.path.getmtime(os.path.join(current_app.config['AVATAR_DEST'], user.avatar)))
    posts = Post.query.filter_by(author=current_user._get_current_object()).order_by(Post.ctime.desc()).limit(5).all()
    # mtime用作查询字符串，头像修改时，强制刷新头像图片
    return render_template('user.html', user=user, mtime=mtime, posts=posts)


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
        # 提交用户头像
        avatar = request.files['avatar']
        fname = avatar.filename
        flag = '.' in fname and \
            fname.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']
        if not flag:
            flash('文件类型错误')
            return redirect(url_for('main.user', username=user.username))
        # /static/avatar/ 文件夹里的保存的用户头像文件名
        flname = user.username + '.' + fname.rsplit('.', 1)[1]
        # 保存头像到指定路径
        avatar.save(os.path.join(current_app.config['AVATAR_DEST'], flname))
        user.avatar = flname
        db.session.add(user)
        db.session.commit()
        flash('用户的个人资料已更新')
        return redirect(url_for('main.user', username=user.username))
    form.avatar.data = os.path.join(current_app.config['AVATAR_DEST'], user.avatar)
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('auth/edit_profile.html', form=form, user=user)


# 写文章
@main.route('/write', methods=['GET', 'POST'])
def write():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        flash('保存成功')
        return redirect(url_for('main.index'))
    return render_template('write.html', form=form)


# 显示文章界面
@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    return render_template('post.html', posts=[post])


# 编辑文章
@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMIN):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('文章已更新')
        return redirect(url_for('main.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)