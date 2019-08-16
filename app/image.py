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
    # 缩放后的头像
    re_im = cr_im.resize((50, 50))  
    # 头像的文件名
    flname = current_user.username + '.jpg'
    # 保存头像到指定路径
    re_im.save(os.path.join(current_app.config['AVATAR_DEST'], flname))
    current_user.avatar = flname
    return True