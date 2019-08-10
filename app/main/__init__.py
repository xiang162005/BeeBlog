from flask import Blueprint

# 创建蓝本
main = Blueprint('main', __name__)

from . import views, errors
from ..models import Permission

# 把Permission加入上下文
# 使得模板在需要检查用户权限时，可以直接使用Permission
# 不用频繁在render_template中传人(Permission=Permisson)
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)