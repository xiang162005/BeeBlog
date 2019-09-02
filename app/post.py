import re
from . import db
from . models import Post


# 生成文章的标签
def create_abstract(id):
    post = Post.query.filter_by(id=id).first()
    if not post:
        flash('没有此文章')
    abstract = re.sub('<[^>]+>', '', post.body_html)
    try:
        post.abstract = abstract[60]
    except IndexError:
        post.abstract = abstract
    else:
        post.abstract = abstract[0:60] + '...'
    db.session.add(post)
    db.session.commit()
