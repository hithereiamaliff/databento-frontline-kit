# Databento frontline kit

Frontline support for Databento's Python client, done for real:
- **a preflight checker** that answers the first questions about a customer's request before anyone downloads data
- **six worked cases** from APAC hours, each run against the live API
- **a one-page playbook** for running the queue from UTC+8

Built on 26 November 2026, as a work sample for Databento's Technical Support Engineer (L1/Frontline Support), APAC role. It uses databento 0.90.0 and a new account's free data credit.

## preflight

Give it what the customer says they ran, exactly as they wrote it, plus their time zone:

```text
python preflight.py --dataset GLBX.MDP3 --schema ohlcv-1h --symbols ESZ6 \
    --start 2026-11-23 --end 2026-11-24 --tz Asia/Kuala_Lumpur
```

```text
[OK] API key accepted
[OK] Dataset GLBX.MDP3 exists
[OK] Schema ohlcv-1h is available for GLBX.MDP3
[WARN] "2026-11-23" has no time zone, so Databento reads it as Mon 2026-11-23 00:00 UTC.
       That's Mon 2026-11-23 08:00 in Asia/Kuala_Lumpur. If you meant Asia/Kuala_Lumpur
       time, send "2026-11-23T00:00:00+08:00" instead. ...
[INFO] The end is exclusive: the last record returned is just before Tue 2026-11-24 00:00
       UTC.
[OK] The whole window is inside the available range
[OK] Every day in the window is marked available (1 day)
[OK] ESZ6 resolves to instrument_id 10252
[INFO] Estimated cost US$0.000228 for 23 records (1,288 billable bytes).

The window in three time zones (start inclusive, end exclusive):
  UTC (as Databento reads it)   Mon 2026-11-23 00:00  to  Tue 2026-11-24 00:00
  Asia/Kuala_Lumpur (customer)  Mon 2026-11-23 08:00  to  Tue 2026-11-24 08:00
  America/Chicago (exchange)    Sun 2026-11-22 18:00  to  Mon 2026-11-23 18:00
```

**What it checks.** It makes only metadata and symbology calls, so nothing is downloaded:
- that the key works, without ever printing it, and what's wrong with its shape if it doesn't (spaces, quotes, length, the wrong variable name)
- that the dataset and schema exist, and the window is inside the available range
- whether any day is flagged `degraded`, `pending` or `missing`
- which symbols don't resolve, with the likely fix, whether a continuous symbol rolled, and how many instruments a parent covers
- the window in UTC, in the customer's time zone and in exchange time, with warnings for plain dates read as UTC, filled-in ends, weekends and UTC daily bars
- the cost, the record count and the billable size

The output is plain text, so it can go straight into a reply or a ticket. It exits with 1 when something blocks the request.

## The cases

| Case | The question | What the run settled |
|---|---|---|
| [01](cases/01-daily-bars-dont-match/) | My daily bars don't match my broker's chart | `ohlcv-1d` is UTC days, and the run proves it. CME sessions and Penang days give different closes every day |
| [02](cases/02-no-data-for-es/) | I asked for ES and got nothing | "ES" isn't a symbol. `get_range` returns nothing with an easy-to-miss warning, while `get_cost` raises a 422 |
| [03](cases/03-bill-higher-than-expected/) | My bill was higher than I expected | The schema drives the cost. Parent symbols matter for CL, not much for ES. A 10-minute-rounded estimate came out 19% too high |
| [04](cases/04-authentication-error/) | I get an authentication error | A stray line break or quotes give a 400 that repeats the key back |
| [05](cases/05-nan-symbols-issue-147/) | `to_df()` gives me NaN symbols | Issue #147. It's intermittent, because the symbol mappings come back in a different order between reads |
| [06](cases/06-monday-starts-at-8am/) | I asked for Monday, but my data starts at 8am | Plain dates are UTC. An offset like `+08:00` fixes it |

Each case has the reply I'd send, what the run showed, and a [transcript](cases/06-monday-starts-at-8am/transcript.md) of the real run. Where the team should hear about something, there's a short note.

## What turned up along the way

These came from running the cases, not from reading about them:

1. **A key with a stray line break or quotes gets a 400 that includes the key.** Customers paste errors into Slack and GitHub. ([case 04](cases/04-authentication-error/))
2. **Issue #147 is intermittent.** `Metadata.mappings` comes back in a different order between reads of the same file, and `to_df()` rebuilds the symbol map on every call. So the same download loses symbols on some calls and not others: 5 of 10 here. ([case 05](cases/05-nan-symbols-issue-147/))
3. **Every Sunday in November 2026 is flagged degraded on GLBX.MDP3,** and no other day since August. Nothing on the status page explains it. ([known issues](cases/known-issues.md#every-sunday-in-november-is-flagged-degraded-on-glbxmdp3))
4. **With pandas 3.1, `to_df()` prints a deprecation warning on every call,** because the client uses `inplace=True`. ([known issues](cases/known-issues.md#to_df-prints-a-pandas-deprecation-warning-on-every-call))
5. **For a symbol that doesn't resolve, `get_range` warns and returns nothing, while `get_cost` raises a 422.** ([case 02](cases/02-no-data-for-es/))

None of these has been reported upstream yet.

## The playbook

[PLAYBOOK.md](PLAYBOOK.md) covers:
- who's awake at each hour of a Penang shift, and what the markets are doing then
- what L1 can settle alone, and what to escalate
- an escalation template and a shift handoff note
- the FAQ entries these cases suggest

## Run it

You need Python 3.11 or later, and a Databento account for the live parts. New accounts get US$125 of free credit.

```text
python -m venv .venv
.venv\Scripts\activate          # macOS or Linux: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # macOS or Linux: cp .env.example .env
```

Then paste your key into `.env` after `DATABENTO_API_KEY=`.

```text
python -m pytest                # 41 offline tests: no key, no network
python preflight.py --help
python cases/record.py          # runs every case live and rewrites the transcripts
```

## Safety and cost

- **The key is never printed.** It's read from `.env` or the environment, and every report and transcript is scrubbed of it. That includes the base64 form HTTP Basic auth uses, and anything shaped like a Databento key.
- **Every download is priced first.** A case stops if one download is estimated above US$0.50.
- **One full run of every case costs about US$0.06 of data credit.** Building and testing the whole kit used well under US$1 of the free US$125.

## Tests

`python -m pytest` runs 41 tests offline, using a fake client that answers in the same shapes as Databento's API:
- time windows: UTC by default, offsets, filled-in ends, weekends, CME trading dates
- key checks and scrubbing
- preflight's logic
- the issue #147 ordering bug

## Licence

MIT, by Aliff. The kit uses databento-python (Apache 2.0) as a dependency; none of its code is copied here.
