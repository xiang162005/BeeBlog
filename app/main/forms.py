from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, SubmitField, TextAreaField, \
    SelectField, FileField
from wtforms.validators import DataRequired, Length, Email, Regexp
from wtforms import ValidationError
from ..models import User, Role


# 管理员的用户资料编辑表单
class EditProfileAdminForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0,
        '用户名必须由英文字母、数字、下划线组成，'
        '并且第一个字符必须是英文字符。')])
    confirmed = BooleanField('确认注册')
    role = SelectField('角色', coerce=int)
    # 头像
    avatar = FileField('头像')
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('所在地', validators=[Length(0, 64)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('保存')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.id).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and \
                User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

    def validate_username(self, field):
        if field.data != self.user.username and \
                User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')


# 写文章表单
class PostForm(FlaskForm):
    title = StringField('标题', validators=[DataRequired()])
    body = PageDownField('正文', validators=[DataRequired()])
    submit = SubmitField('保存')


# 写评论表单
class CommentForm(FlaskForm):
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('保存')