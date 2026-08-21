# Storage

Finpipe uses PostgreSQL through SQLAlchemy and Alembic.

Persistent user data includes access roles, company and bank-account details, invoice settings, encrypted signatures, Telegram state, audit logs, application events, and document-generation history.

Generated PDF and DOCX files are delivery artifacts, not persistent records. The Telegram delivery workflow removes them after every delivery attempt. Encrypted signature files remain persistent because they are source data required for later document generation.

Apply schema migrations with:

```bash
poetry run alembic upgrade head
```
