"""users表加入name, location, about_me, member_since, last_login

Revision ID: 93eb7168e081
Revises: 10b783bddfb8
Create Date: 2019-08-10 19:51:16.980073

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '93eb7168e081'
down_revision = '10b783bddfb8'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('about_me', sa.Text(), nullable=True))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('location', sa.String(length=64), nullable=True))
    op.add_column('users', sa.Column('member_since', sa.DateTime(), nullable=True))
    op.add_column('users', sa.Column('name', sa.String(length=64), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('users', 'name')
    op.drop_column('users', 'member_since')
    op.drop_column('users', 'location')
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'about_me')
    # ### end Alembic commands ###
