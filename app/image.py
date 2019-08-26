import os
from flask import current_app
from flask_login import current_user
from PIL import Image
from . import db
from .models import User

# 生成头像，成功返回True, 失败返回False
def create_avatar(avatar):
    fname = avatar.filename
    flag = '.' in fname and \
        fname.rsplit('.', 1)[1] in current_app.config['ALLOWED_EXTENSIONS']
    if not flag:
        return False
    # 打开要缩放的头像（转换成RGB便于保存头像时把png等格式统一转化为jpg）
    im = Image.open(avatar).convert('RGB')
    # 头像的宽和高
    w, h =im.size
    # 短边长度的一半，用于定位
    half = (w // 2) if (w <= h) else (h // 2)
    # 裁剪头像的左、右、上、下坐标
    left = w // 2 - half
    right = w // 2 + half
    top = h // 2 - half    
    bottom =  h // 2  + half
    # 裁剪成正方形的头像
    cr_im = im.crop((left, top, right, bottom))
    # 缩放后的大头像
    b_im = cr_im.resize((128, 128))
    # 缩放后的小头像
    s_im = cr_im.resize((50, 50))  
    # 大头像的文件名
    b_flname = current_user.username + '/big.jpg'
    # 小头像的文件名
    s_flname = current_user.username + '/small.jpg'
    # 保存大头像到指定路径
    b_im.save(os.path.join(current_app.config['AVATAR_DEST'], b_flname))
    # 保存小头像到指定路径
    s_im.save(os.path.join(current_app.config['AVATAR_DEST'], s_flname))
    current_user.b_avatar = b_flname
    current_user.s_avatar = s_flname
    return True