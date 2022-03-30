"""initial migration

Revision ID: e0e440c4486d
Revises: 
Create Date: 2022-03-30 23:45:37.915723

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e0e440c4486d'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        'ticker',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('name', sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ticker_name'), 'ticker', ['name'], unique=False)
    op.create_table(
        'ticker_price',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('ticker_id', sa.BigInteger(), nullable=False),
        sa.Column('price', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(
            ['ticker_id'],
            ['ticker.id'],
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_ticker_price_ticker_id'), 'ticker_price', ['ticker_id'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_ticker_price_ticker_id'), table_name='ticker_price')
    op.drop_table('ticker_price')
    op.drop_index(op.f('ix_ticker_name'), table_name='ticker')
    op.drop_table('ticker')
    # ### end Alembic commands ###
