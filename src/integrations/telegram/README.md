# Telegram Integration

The main user interface for Finpipe. Reply keyboard for navigation, one-time keyboard for in-flow actions.

---

## Architecture

```
Telegram Update
      │
      ▼
  TelegramBot          ← receives updates, handles authorization and state
      │
      ▼
  CommandRouter        ← routes by button text / command, writes audit log
      │
      ▼
  Domain Handler       ← Telegram-specific logic
      │
      ▼
  Service / Workflow   ← business logic
      │
      ▼
  Storage              ← PostgreSQL
```

---

## Menu structure

```
/start → Main menu
├── 📄 Documents
│   ├── 🧾 Invoice
│   │   ├── 💰 Set amount
│   │   ├── 💶 Current amount
│   │   └── 📄 Generate → [📤 Send to company | ✖️ Skip]
│   └── 🏦 Bank day → info screen [▶️ Run | 🏠 Home]
│       └── ▶️ Run → workflow → [📤 Reply to bank | ✖️ Skip]
├── 📧 Integrations → Gmail
│   ├── 🔗 Connect / ❌ Disconnect
│   ├── 📊 Status
│   ├── 🏠 Home
│   └── 🗑 Reset history → [🗑 Yes, reset | ✖️ Cancel]
├── 👤 My profile
│   ├── 👁 View profile / 👤 Who am I
│   ├── 📥 Download template / 📤 Update profile
│   ├── ✍️ Upload signature / 🗑 Delete signature
│   └── 🏠 Home
└── 📖 Help
    ├── ❓ How to start / ✅ Readiness
    └── 🏠 Home
```

Owner also gets `🛠️ Admin` in the main menu, with a user management submenu.

---

## Button types

- **Reply keyboard** — navigation between sections (stays visible)
- **One-time reply keyboard** — single-action choices (send / skip)

---

## Roles

| Role | Access |
|---|---|
| Guest | `👤 Who am I` only |
| User | Profile, documents, Gmail |
| Owner | Everything + user management |

---

## Handlers

| Handler | Purpose |
|---|---|
| `command_router.py` | Routes all commands, writes audit log |
| `menu_handlers.py` | Menu navigation |
| `profile_handlers.py` | Profile, template, view |
| `signature_handlers.py` | Upload and delete signature |
| `gmail_handlers.py` | Gmail connect / disconnect / status / history |
| `document_handlers.py` | Invoice, bank day |
| `owner_handler.py` | User management |
| `system_handlers.py` | Help, readiness, whoami |
| `monitoring_handler.py` | Monitoring chat commands |

---

## Adding a new command

1. Add a constant to `ui/buttons/`
2. Add it to the menu if needed
3. Implement the method in a handler
4. Register in `CommandRouter._build_command_handlers()`
5. Write a test
