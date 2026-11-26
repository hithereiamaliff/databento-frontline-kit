# Known issues and ready replies

Checked on 26 Nov 2026 against databento 0.90.0. The first two are on GitHub. The rest turned up while building this kit, and none of them has been reported anywhere yet.

## On GitHub

### #142: `pip install databento` fails on Python 3.15 (closed)

- **Symptom:** `Could not find a version that satisfies the requirement databento-dbn~=0.70.0`.
- **Status:** fixed in databento 0.90.0 (3 Nov 2026), which requires databento-dbn 0.73, the first release with Python 3.15 wheels.
- **Reply:**
  > Hi! That's fixed in databento 0.90.0. Run `pip install -U databento` and it will pick up a compatible databento-dbn. New releases usually come out on Tuesdays.

### #141: the live client's reconnect gives up after one attempt (closed, by design)

- **Symptom:** with `reconnect_policy="reconnect"`, a failed reconnection stops the client, and the customer's loop waits forever without an exception.
- **Status:** by design. The maintainer said logging would improve in the next release, and that a docs note is staged.
- **Reply:**
  > Hi! The client only gets a chance to raise when your code hands control back to it. Use `Live.block_for_close()` or `Live.wait_for_close()`, and you'll get an exception when a reconnect fails, which you can handle by starting a new session. The reconnect logic makes a single attempt; the docs will say so soon.
- **Not reproduced here:** it needs a live data subscription.

### #147: NaN symbols from `to_df()` (open)

See [case 05](05-nan-symbols-issue-147/). It's intermittent, and the case shows why.

## Found while building this kit

### Every Sunday in November is flagged degraded on GLBX.MDP3

- **What I saw:** `metadata.get_dataset_condition` marks 1, 8, 15 and 22 Nov 2026 as `degraded`. They're all Sundays, and no other day since 1 Aug is flagged.
- **What customers see:** a request that touches one of those Sundays prints a BentoWarning: "The streaming request contained one or more days which have reduced quality". Cases [01](01-daily-bars-dont-match/) and [06](06-monday-starts-at-8am/) both hit it.
- **What I checked:** the status page and the release notes, on 26 Nov. Neither mentions it.
- **Reply to a customer, until we know more:**
  > Hi! "Degraded" means the data for that day is available, but may have gaps or other quality issues. On GLBX.MDP3 it currently covers each Sunday in November, which holds only the first hour or so of Monday's session (CME opens at 17:00 Sunday, Chicago time). We're looking into it, and I'll update you here.
- **The escalation:**
  ```text
  Summary: Every Sunday since 1 Nov 2026 is "degraded" on GLBX.MDP3
  Severity: question (degraded, not missing)
  What I ran: metadata.get_dataset_condition("GLBX.MDP3", "2026-08-01", "2026-11-25")
  Expected: Sundays marked "available", as they were from August to October
  Actual: 2026-11-01, 11-08, 11-15 and 11-22 "degraded" (last modified the following
          Monday); nothing else flagged since 1 Aug
  Customer impact: a BentoWarning on any request that touches a Sunday in UTC,
          which includes Monday requests sent in Asian time zones
  Asks: is it known? If it's expected, an FAQ line or a status note would save tickets
  ```

### `to_df()` prints a pandas deprecation warning on every call

- **Symptom:** with pandas 3.1, every `to_df()` prints `Pandas4Warning: The inplace keyword in DataFrame.set_index is deprecated and will be removed in a future version`. It points at `databento/common/dbnstore.py:1538`.
- **Cause:** the client calls `set_index(..., inplace=True)` in `DBNStore._format_set_index`. The Reference API helpers (`adjustment.py`, `corporate.py`, `security.py`) also use `inplace=True` with `set_index`, `sort_index`, `drop` and `sort_values`.
- **Impact today:** noise only. The client requires pandas below 4.0, so nothing breaks yet.
- **Reply:**
  > Hi! That warning comes from inside the client, not from your code, and it's harmless. To hide it, add this after `import databento`:
  > `warnings.filterwarnings("ignore", message="The inplace keyword", category=DeprecationWarning)`.
  > It has to come after the import, because importing the client turns pandas' warnings back on.
- **For the maintainers:** assign the result instead, for example `df = df.set_index(index_column)`, and return the new frame.

### A key with stray characters is repeated back in the 400 error

See [case 04](04-authentication-error/). The `auth_invalid_username_in_basic_auth` message includes the submitted key, so customers who paste the error publicly leak it.

### For an unresolvable symbol, `get_range` and `get_cost` disagree

See [case 02](02-no-data-for-es/). `get_range` returns nothing and warns, while `get_cost` raises a 422 for the same request.
