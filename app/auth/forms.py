from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, \
    TextAreaField
from wtforms.validators import DataRequired, Length, Email, Regexp, EqualTo
from wtforms import ValidationError
from ..models import User


# 登陆表单
class LoginForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                             Email()])
    password = PasswordField('密码', validators=[DataRequired()])
    remember_me = BooleanField('记住登陆状态')
    submit = SubmitField('登陆')


# 注册表单
class RegistrationForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    username = StringField('用户名', validators=[
        DataRequired(), Length(1, 64),
        Regexp('^[A-Za-z][A-Za-z0-9_]*$', 0, 
               '用户名必须由英文字母、数字、下划线组成，'
               '并且第一个字符必须是英文字符。')])
    password = PasswordField('密码', validators=[
        DataRequired(), EqualTo('password2', message='两次密码不一致')])
    password2 = PasswordField('确认密码', validators=[DataRequired()])
    submit = SubmitField('注册')
        
    # 验证邮箱是否已被注册
    def validate_email(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')

    # 验证用户名是否已被注册
    def validate_username(self, field):
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('用户名已存在')


# 修改密码表单
class ChangePasswordForm(FlaskForm):
    oldpassword = PasswordField('原密码', validators=[DataRequired(), Length(1, 64)])
    newpassword = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('newpassword2', message='两次密码不一致')])
    newpassword2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('修改密码')


# 请求重设密码表单
class ResetPasswordRequestForm(FlaskForm):
    email = StringField('邮箱', validators=[DataRequired(), Length(1, 64),
                                            Email()])
    submit = SubmitField('发送重设密码邮件')


# 重设密码表单
class ResetPasswordForm(FlaskForm):
    newpassword = PasswordField('新密码', validators=[
        DataRequired(), EqualTo('newpassword2', message='两次密码不一致')])
    newpassword2 = PasswordField('确认新密码', validators=[DataRequired()])
    submit = SubmitField('重设密码')


# 请求修改邮箱
class ChangeEmailRequestForm(FlaskForm):
    newemail = StringField('新的邮箱', validators=[DataRequired(), Length(1, 64),
                                                  Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('修改邮箱')
    
    # 验证邮箱是否已被注册
    def validate_newemail(self, field):
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('邮箱已被注册')


# 个人资料编辑器
class EditProfileForm(FlaskForm):
    name = StringField('昵称', validators=[Length(0, 64)])
    location = StringField('所在地', validators=[Length(0, 64)])
    about_me = TextAreaField('个人简介')
    submit = SubmitField('保存')
    