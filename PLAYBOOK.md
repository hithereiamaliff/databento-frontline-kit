# APAC-hours playbook

How I'd run Databento's frontline queue from Penang (UTC+8), 09:00 to 18:00 on weekdays. It's one page on purpose: the details live in the cases.

## 1. Who's awake, and what the markets are doing

Times for November, when the US is on standard time and London on GMT. Between March and early November most US rows move one hour earlier in Penang.

| Penang (UTC+8) | UTC | Salt Lake City | Chicago (CME) | London | What's happening |
|---|---|---|---|---|---|
| 06:00 | 22:00 | 15:00 | 16:00 | 22:00 | CME Globex closes for its daily break (Friday: for the weekend) |
| 07:00 | 23:00 | 16:00 | 17:00 | 23:00 | CME Globex reopens. On Monday this is the weekly open |
| 08:00 | 00:00 | 17:00 | 18:00 | 00:00 | A new UTC day: `ohlcv-1d` bars and plain dates in API calls roll over |
| 09:00 | 01:00 | 18:00 | 19:00 | 01:00 | APAC shift starts. Read the US handoff note first |
| 17:00 | 09:00 | 02:00 | 03:00 | 09:00 | London's working day starts |
| 18:00 | 10:00 | 03:00 | 04:00 | 10:00 | APAC shift ends. Hand off to the EU queue |
| 22:30 | 14:30 | 07:30 | 08:30 | 14:30 | US stock market opens (09:30 New York) |

**What that means in practice:**
- For most of the shift, nobody in the US is working. L1 has to settle what it can alone, and leave escalations that engineering can act on without a call.
- APAC customers are usually looking at the overnight futures session, or at yesterday's US session. A "today" in Penang is mostly "yesterday" in Chicago.
- The UTC date changes at 08:00 Penang time. Anything a customer calls "today's data" before 08:00 is still yesterday in UTC.

## 2. What L1 settles alone

| The customer says | First move | Worked case |
|---|---|---|
| "I got no data" or an empty DataFrame | Run `preflight.py` with their exact call: symbols, window, availability | [02](cases/02-no-data-for-es/), [06](cases/06-monday-starts-at-8am/) |
| "Your daily bars are wrong" | Explain UTC days versus sessions, and send the hourly-bar recipe | [01](cases/01-daily-bars-dont-match/) |
| "Why did this cost so much?" or "How much will this cost?" | Price it with `metadata.get_cost`, show what drove the size, and point to the monthly limit | [03](cases/03-bill-higher-than-expected/) |
| "Authentication failed" | Check the key's shape with preflight. If the shape is fine, have them create a new key | [04](cases/04-authentication-error/) |
| A known client bug | Send the workaround, and link the issue so they can follow it | [05](cases/05-nan-symbols-issue-147/), [known issues](cases/known-issues.md) |

## 3. What to escalate

These routes are my guess until I know how the team splits work.

- **The data looks wrong** (a gap on a day marked `available`, an odd price, a missing instrument) goes to engineering. Include the preflight report and a minimal script, plus the exact records: `ts_recv`, `instrument_id` and `sequence`.
- **A client bug that isn't on the known list** goes to the client maintainers. Include a minimal repro and the versions, written so it can become a GitHub issue as it stands.
- **Billing changes** (refunds, credits, cancelling an invoice) go to billing. L1 can explain a bill, but the docs say only support staff can cancel an invoice.
- **Licensing and live-data entitlements** go to sales.
- **Possible outages:** check the status page, then escalate straight away with UTC timestamps.
- **A key posted in public** (on Slack or GitHub): tell the customer to rotate it at once. Databento revokes keys it finds published.

## 4. The escalation template

```text
Summary (one line):
Customer and plan:
Severity: blocking / degraded / question
What they ran (the exact call, or the preflight command):
Versions: client and version, Python, OS
Window in UTC, and in the customer's time zone:
Expected, and what happened instead:
Preflight report: (paste it)
Minimal repro: (a script or steps, with no keys)
What I've told the customer, and when I promised the next update:
```

## 5. The handoff note, at the end of each shift

```text
Open threads (link, one line each, next action, who owns it):
Waiting on engineering:
Promised updates, with times in the receiving team's time zone:
Seen twice today (possible patterns):
```

## 6. FAQ entries these cases suggest

1. Why don't Databento's daily bars match my broker's? ([case 01](cases/01-daily-bars-dont-match/))
2. Why did my request return no data? The four ways to name a future. ([case 02](cases/02-no-data-for-es/))
3. How do I estimate what a request will cost, and cap my spending? ([case 03](cases/03-bill-higher-than-expected/))
4. My key looks right, so why is it rejected? ([case 04](cases/04-authentication-error/))
5. How do I ask for a day in my own time zone? ([case 06](cases/06-monday-starts-at-8am/))

## 7. House rules I'd keep

- Every reply states the time window in UTC and in the customer's time zone.
- Price before downloading, and say what drove the size.
- Never ask for a customer's API key, and never paste one anywhere.
- Write each reply so the customer can act on it without writing back: the fix, the code, and the reason.
