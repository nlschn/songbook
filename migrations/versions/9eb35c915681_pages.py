"""pages

Revision ID: 9eb35c915681
Revises: 
Create Date: 2024-05-28 22:24:06.606926

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9eb35c915681'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('song', schema=None) as batch_op:
        batch_op.add_column(sa.Column('pages', sa.Integer(), nullable=True))
        batch_op.drop_index('ix_song_release_id')
        batch_op.create_index(batch_op.f('ix_song_pages'), ['pages'], unique=False)
        batch_op.drop_column('release_id')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('song', schema=None) as batch_op:
        batch_op.add_column(sa.Column('release_id', sa.VARCHAR(length=500), nullable=True))
        batch_op.drop_index(batch_op.f('ix_song_pages'))
        batch_op.create_index('ix_song_release_id', ['release_id'], unique=False)
        batch_op.drop_column('pages')

    # ### end Alembic commands ###
