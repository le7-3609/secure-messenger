## ✅ What You've Already Implemented

- **`server/broadcaster.py`** — per-recipient pub/sub (actually more advanced than the minimum — it filters by recipient, not broadcast-to-all)
- **`GET /stream`** SSE endpoint
- **`POST /messages`** broadcasts to recipients after saving
- **CLI client** (`client/main.py` + `client/api.py`) — SSE listener thread, send with recipients, graceful quit

---

## ❌ What's Still Missing (Minimum Requirements)

### 1. `seed.py` — entirely absent
The instructions require a script that registers alice/bob/charlie, logs them in, and sends seed messages. You have no such file.

### 2. SSE tests in `tests/test_app.py`
The instructions require these three tests, none of which exist yet:
- `test_sse_stream_receives_broadcast` — send a message, verify it arrives on `/stream`
- `test_only_sender_sees_targeted_messages` — Alice→Bob, Charlie shouldn't receive it
- `test_concurrent_clients` — two clients send simultaneously, both receive both messages

### 3. CLI client UX gaps
Comparing your `client/main.py` to the spec:
- No **register/login choice menu** (`1) Register  2) Login`)  
- Password is read with plain `input()` — should use `getpass` (hidden input)
- No **message history display** on connect (`--- message history ---` block) — `ApiClient` has no `get_messages()` method

---

## 🚀 Beyond Minimum — Bonus Improvements

Your broadcaster is already per-recipient (Bonus 1 is done!). The remaining bonuses, ordered by value:

| Bonus | What it adds | Complexity |
|---|---|---|
| **User presence** (`GET /users/online`) | Show who's connected | Low — broadcaster already tracks subscribers |
| **Token versioning** | New login invalidates old sessions | Medium — add `login_version` to User + JWT |
| **Message edit/delete** | `PATCH`/`DELETE /messages/{id}` with broadcast | Medium-High |

The **presence indicator** is nearly free given your broadcaster design — `self._listeners` already holds the active subscribers, you just need to expose a route that returns its keys.