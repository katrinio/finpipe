# Storage

Finpipe uses PostgreSQL through SQLAlchemy and Alembic.

Persistent data includes company and bank-account details, invoice and latest bank amounts, encrypted signatures, Telegram workflow state, and the Telegram update checkpoint. Authorization comes directly from `BOT_OWNER_TELEGRAM_ID` and is not stored in PostgreSQL.

Generated PDF and DOCX files are delivery artifacts, not persistent records. The Telegram delivery workflow removes them after every delivery attempt. Encrypted signature files remain persistent because they are source data required for later document generation.

Apply schema migrations with:

```bash
poetry run alembic upgrade head
```
