# The cases

Six questions a frontline engineer might get during APAC hours, each run against the real API on 26 Nov 2026.

| Case | The question | What the run settled | Kind |
|---|---|---|---|
| [01](01-daily-bars-dont-match/) | My daily bars don't match my broker's chart | `ohlcv-1d` is UTC days, and the run proves it. Session bars and Penang days give different closes every day | Documented; FAQ candidate |
| [02](02-no-data-for-es/) | I asked for ES and got nothing | "ES" isn't a symbol. `get_range` returns nothing with an easy-to-miss warning, while `get_cost` raises a 422 | User error; note for the team |
| [03](03-bill-higher-than-expected/) | My bill was higher than I expected | The schema drives the cost. Parent symbols matter for CL, not much for ES. Estimates round up to 10 minutes: one came out 19% too high | Billing; documented |
| [04](04-authentication-error/) | I get an authentication error | A stray line break or quotes give a 400 that repeats the key back, which is a security note | User error; security note |
| [05](05-nan-symbols-issue-147/) | `to_df()` gives me NaN symbols | Issue #147, reproduced offline and live. It's intermittent because the symbol order changes between reads | Bug, open upstream |
| [06](06-monday-starts-at-8am/) | I asked for Monday, but my data starts at 8am | Plain dates are UTC, so a Penang Monday starts at 8am. An offset like `+08:00` fixes it | User error; documented |

Each folder has:
- **README.md:** the question, the reply I'd send, what the run showed, and a note for the team where one's needed
- **run.py:** the reproduction. Every download is priced first and capped at US$0.50
- **transcript.md:** exactly what the run printed, recorded by `record.py`

Also here:
- **[known-issues.md](known-issues.md):** ready replies for known issues, plus what turned up while building this kit
- **record.py:** runs every case and rewrites the transcripts. One full run costs about US$0.06 of data credit
