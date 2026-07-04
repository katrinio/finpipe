# Gmail OAuth

## Connection flow

```
Telegram                     Bot                        Google OAuth
─────────                   ─────                       ────────────
[📧 Gmail → 🔗 Connect]
                     ──► GmailHandlers.gmail_connect()
                     ──► GmailOAuth.build_authorization_url()
                     ──► OAuthSession saved to DB
                     ◄── inline button with Google URL
[taps 🔗 Connect Gmail]
                                            ──► Google OAuth consent screen
                                            ◄── redirect → /oauth/gmail/callback
                     GmailOAuthCallbackService.handle_callback()
                     ──► validate state from OAuthSession
                     ──► code → refresh_token (token exchange)
                     ──► GmailAccount updated in DB
                     ──► OAuthSession marked as used
                     ──► AuditLog: gmail_oauth_callback SUCCESS
[📊 Status → ✅ Gmail connected]
```

---

## Callback endpoint

| Parameter | Value |
|---|---|
| Method | `GET` |
| Path | `/oauth/gmail/callback` |
| Query params | `code`, `state`, `error` |

The route contains no business logic — it accepts the parameters, delegates to `GmailOAuthCallbackService`, and returns an HTML response.

| Result | Browser response |
|---|---|
| ✅ Success | `Gmail successfully connected. You may close this browser window.` |
| ❌ Error | `Gmail connection failed. <reason>` (HTTP 400) |

Both outcomes are recorded in `AuditLog` under the `gmail_oauth_callback` command.

---

## Configuration

### Callback URL

| Variable | Purpose |
|---|---|
| `GMAIL_OAUTH_CALLBACK_URL` | The only source of truth for the callback URL — used when building the authorization URL and during token exchange |
| `GMAIL_OAUTH_CALLBACK_ENABLED` | Set to `true` to enable callback handling |

> ⚠️ Updating `.env` does not update Google Cloud Console. When the callback URL changes, add the new URI to `Authorized redirect URIs` in your OAuth client.

### OAuth client credentials

Resolved in priority order:

| Source | Condition |
|---|---|
| `GMAIL_CLIENT_ID` + `GMAIL_CLIENT_SECRET` | if both are set in env |
| `GMAIL_CREDENTIALS_PATH` | fallback — `credentials.json` file |

### Gmail scopes

```
https://www.googleapis.com/auth/gmail.readonly
https://www.googleapis.com/auth/gmail.send
```

---

## Token storage

| Table | What's stored |
|---|---|
| `oauth_session` | Temporary OAuth session (state, expires_at, status) |
| `gmail_account` | Encrypted refresh token, gmail_email, last_error |

The refresh token is encrypted via `TokenCipher` before saving.

On every `get_gmail_service()` call:
- token is refreshed via `credentials.refresh(Request())`
- on `RefreshError` — error is written to `gmail_account.gmail_last_error`, returns `None`
- on success — `gmail_last_error` is cleared

---

## Local development

To debug OAuth via Cloudflare Quick Tunnel:

**1.** Start FastAPI locally (usually `http://127.0.0.1:8000`)

**2.** Run the tunnel:

```bash
./scripts/start_oauth_tunnel.sh
# or with a different port:
PORT=8080 ./scripts/start_oauth_tunnel.sh
```

The script:
- starts `cloudflared tunnel --url http://127.0.0.1:8000`
- builds `https://<tunnel-host>/oauth/gmail/callback`
- writes `GMAIL_OAUTH_CALLBACK_URL` to `.env`

**3.** Copy the printed `OAuth Redirect URI` → add it in Google Cloud Console → `Authorized redirect URIs`

**4.** Make sure `.env` has:
```
GMAIL_OAUTH_CALLBACK_ENABLED=true
GMAIL_OAUTH_CALLBACK_URL=https://<tunnel-host>/oauth/gmail/callback
```

**5.** In Telegram: `📧 Gmail` → `🔗 Connect` → `🔗 Connect Gmail`

> ⚠️ The Quick Tunnel URL changes on every script restart — update the redirect URI in Google Cloud Console each time.

---

## Diagnostics

| Symptom | What to check |
|---|---|
| `📊 Status` shows `unknown` instead of email | `gmail_account.gmail_email` is empty — reconnect |
| `📊 Status` shows an error | `gmail_account.gmail_last_error` — token was revoked, reconnect |
| Callback unreachable | `GMAIL_OAUTH_CALLBACK_ENABLED=true` in `.env` |
| `redirect_uri_mismatch` | Callback URL in `.env` doesn't match Google Cloud Console |
| `AuditLog` shows FAILED for `gmail_oauth_callback` | Token exchange error — check server logs |
