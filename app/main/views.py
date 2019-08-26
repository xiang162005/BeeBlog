import os
from datetime import datetime
from flask import render_template, redirect, request, url_for, flash, \
    current_app
from flask_login import current_user, login_required
from . import main
from .forms import EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import User, Permission, Post, Comment
from ..decorators import admin_required, permission_required

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
    mtime = str(os.path.getmtime(os.path.join(current_app.config['AVATAR_DEST'], user.b_avatar)))
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
@login_required
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
@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    post = Post.query.get_or_404(id)
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          post=post,
                          author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('成功发表评论')
        # page=-1为最后一页评论，以便显示刚提交的评论
        return redirect(url_for('main.post', id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        # 计算最后一页
        page = (post.comments.count() - 1) // \
            current_app.config['COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page, per_page=current_app.config['COMMENTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items
    return render_template('post.html', posts=[post], form=form,
                            comments=comments, pagination=pagination)


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


# 关注用户
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        flash('您已经关注了{}'.format(username))
        return redirect(url_for('main.user', username=username))
    current_user.follow(user)
    db.session.commit()
    flash('成功关注{}'.format(username))
    return redirect(url_for('main.user', username=username))


# 取消关注用户
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        flash('您还没有关注{}'.format(username))
        return redirect(url_for('main.user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash('成功取消关注{}'.format(username))
    return redirect(url_for('main.user', username=username))


# 粉丝列表
@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.follower.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="的粉丝列表",
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)


# 关注用户的列表
@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('没有此用户')
        return redirect(url_for('main.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp}
               for item in pagination.items]
    return render_template('followers.html', user=user, title="关注的用户列表",
                           endpoint='main.followers', pagination=pagination,
                           follows=follows)


# 我的关注页面
@main.route('/followed_posts')
@login_required
def followed_posts():
    # 我关注的用户的文章
    q1 = current_user.followed_posts
    # 我写的文章
    q2 = current_user.posts
    # 关注的用户的文章加上我写的文章
    query = q1.union(q2)
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.ctime.desc()).paginate(
        page, per_page=current_app.config['POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items
    return render_template('followed_posts.html', posts=posts, pagination=pagination)
    