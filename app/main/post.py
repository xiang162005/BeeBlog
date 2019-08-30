import re
from .. import db
from .. models import Post


# 生成文章的标签
def create_abstract(id):
    post = Post.query.filter_by(id=id).first()
    if not post:
        flash('没有此文章')
    try:
        abstract = post.body_html[60]
    except IndexError:
        abstract = post.body_html
    else:
        abstract = post.body_html[60] + '...'
    post.abstract = re.sub('<[^>]+>', '', abstract)
    db.session.add(post)
    db.session.commit()
