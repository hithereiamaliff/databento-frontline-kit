# 04. "I get an authentication error"

**Kind:** user error (key formatting), plus a security note for the team: one of these errors repeats the key back.

## The question

> My key works in my notebook, but my script fails with `BentoClientError 400 auth_invalid_username_in_basic_auth`. I've checked the key three times and it's right!

## The reply I'd send

> Hi! That error means the key reached us with extra characters around it, usually a line break or quotes picked up when it was read from a file. A key that's simply wrong gets a different error: `401 auth_authentication_failed`.
>
> The quick fixes:
> - If you read the key from a file, strip it: `key = Path("key.txt").read_text().strip()`
> - If it's in a `.env` file or an environment variable, remove any quotes or spaces around it. Note that the client only reads `DATABENTO_API_KEY`.
>
> One important thing: that 400 message includes the key you sent. If you've pasted the error anywhere public, such as Slack, GitHub or a forum, please rotate the key now. You'll find it on the API keys page in the portal.

## What the run showed

From [transcript.md](transcript.md), recorded 26 Nov 2026. Every key in the run is made up, so no real key appears anywhere:

| The customer's mistake | What they see |
|---|---|
| No key at all | `ValueError: invalid API key, was None` |
| A well-formed key that isn't valid | `401 auth_authentication_failed: Authentication failed.` |
| The key with a line break on the end | `400 auth_invalid_username_in_basic_auth: Invalid username in Basic auth ('<the key and the line break>')` |
| The key pasted with its quotes | The same 400, with the quoted key in the message |
| Saved as `DATABENTO_KEY` instead of `DATABENTO_API_KEY` | `ValueError: invalid API key, was None` |

preflight's key check catches four of the five before any request is sent, and says what to fix. The well-formed but invalid key is the exception, since only Databento can tell whether a key is valid. The real key from `.env` was accepted, and it's never printed.

## A note for the team (security)

- **The 400 error repeats the key.** The `auth_invalid_username_in_basic_auth` message includes the submitted username, which is the customer's API key plus the stray characters. Customers paste errors into Slack and GitHub, so this can publish a live key. It would be safer not to echo the username, or to show only its last four characters.
- **The client could catch these mistakes before sending.** It rejects only empty or all-whitespace keys. Stripping whitespace, or raising a clear local error for a key that isn't 32 characters starting with `db-`, would turn this ticket into a one-line message.
- **The missing-key message could name the fix.** "invalid API key, was None" could say: "No API key: pass key= or set DATABENTO_API_KEY."

## Run it

```text
python cases/04-authentication-error/run.py
```
