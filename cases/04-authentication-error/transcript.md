# Transcript: authentication error

Recorded 2026-11-26 04:34 UTC with databento 0.90.0, pandas 3.1.1 and Python 3.13.7 on Windows 11. Produced by `python cases/record.py`; nothing here was edited by hand.

`python cases/04-authentication-error/run.py` (exit code 0)

```text

1. What the customer sees
-------------------------

a) No key anywhere: db.Historical()
  Result: ValueError: invalid API key, was None

b) A well-formed key that isn't valid
  Result: BentoClientError 401
  auth_authentication_failed
  Authentication failed.
  documentation: https://databento.com/docs/portal/api-keys

c) The same key with a line break on the end
  Result: BentoClientError 400
  auth_invalid_username_in_basic_auth
  Invalid username in Basic auth ('db-[redacted]
  ').
  documentation: https://databento.com/docs

d) The same key pasted with its quotes
  Result: BentoClientError 400
  auth_invalid_username_in_basic_auth
  Invalid username in Basic auth ('"db-[redacted]"').
  documentation: https://databento.com/docs

e) Key saved as DATABENTO_KEY instead of DATABENTO_API_KEY
  Result: ValueError: invalid API key, was None

2. What preflight's key check says for each
-------------------------------------------
a) No API key found. Set DATABENTO_API_KEY in the environment or in .env.
b) Right shape, so only Databento can say whether it's valid: the server answers 401.
c) The key has a space or line break before or after it.
d) The key is wrapped in quotes. Paste it without them.
e) No API key found. Set DATABENTO_API_KEY in the environment or in .env. Something is saved under DATABENTO_KEY, but the client only reads DATABENTO_API_KEY.

3. The real key from .env (never printed)
-----------------------------------------
Accepted. This account can see 31 datasets.
```
