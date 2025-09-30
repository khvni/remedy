from alembic import op
import sqlalchemy as sa

revision = '0001_init'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('repos',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('name', sa.String, nullable=False),
        sa.Column('url', sa.String, nullable=False),
        sa.Column('default_branch', sa.String, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_table('scans',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('repo_id', sa.String, sa.ForeignKey('repos.id')),
        sa.Column('kind', sa.String, nullable=False),
        sa.Column('status', sa.String, nullable=False),
        sa.Column('findings_json', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )
    op.create_table('findings',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('scan_id', sa.String, sa.ForeignKey('scans.id')),
        sa.Column('severity', sa.String, nullable=False),
        sa.Column('path', sa.String, nullable=False),
        sa.Column('line', sa.Integer, nullable=True),
        sa.Column('rule_id', sa.String, nullable=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('plan_json', sa.JSON, nullable=True),
    )
    op.create_table('pull_requests',
        sa.Column('id', sa.String, primary_key=True),
        sa.Column('repo_id', sa.String, sa.ForeignKey('repos.id')),
        sa.Column('branch', sa.String, nullable=False),
        sa.Column('pr_url', sa.String, nullable=True),
        sa.Column('status', sa.String, nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False),
    )

def downgrade():
    op.drop_table('pull_requests')
    op.drop_table('findings')
    op.drop_table('scans')
    op.drop_table('repos')
