from flask import render_template
from . import main



# 主页视图函数
@main.route('/')
def index():
    return render_template('index.html')
