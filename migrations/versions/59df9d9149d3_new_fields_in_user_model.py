"""new fields in user model

Revision ID: 59df9d9149d3
Revises: 20415b1841d4
Create Date: 2022-05-17 19:42:03.533880

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '59df9d9149d3'
down_revision = '20415b1841d4'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('last_seen', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('registered', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'registered')
    op.drop_column('user', 'last_seen')
    # ### end Alembic commands ###
