# 02. "I asked for ES and got nothing"

**Kind:** user error (symbology), plus a note for the team about how quietly it fails.

## The question

> I'm calling `get_range` on GLBX.MDP3 with `symbols="ES"` and getting an empty DataFrame. No error. ES is one of the most traded futures in the world, so where is it?

## The reply I'd send

> Hi! At CME, "ES" is the product, not a symbol you can request on its own. Each contract has its own name, like ESZ6 for December 2026. When none of the symbols in a request match anything, `get_range` returns no data and warns you rather than raising an error. You'll have seen this in your output: "The streaming request had one or more symbols which did not resolve: ES."
>
> Pick the form that fits what you want:
>
> | You want | symbols | stype_in |
> |---|---|---|
> | One contract | `["ESZ6"]` | `"raw_symbol"` (the default) |
> | The front month, rolling automatically | `["ES.c.0"]` | `"continuous"` |
> | Every ES contract and calendar spread | `["ES.FUT"]` | `"parent"` |
>
> You can check how a symbol resolves before downloading anything. This call is free:
>
> ```python
> client.symbology.resolve(
>     dataset="GLBX.MDP3", symbols=["ES.c.0"], stype_in="continuous",
>     stype_out="instrument_id", start_date="2026-11-23", end_date="2026-11-24",
> )
> ```

## What the run showed

From [transcript.md](transcript.md), recorded 26 Nov 2026, for Monday 23 Nov:

- **`symbols="ES"` on its own:** 0 rows and no exception, just two warnings: "No data found for the request you submitted." and "...did not resolve: ES."
- **`symbols=["ES", "ESZ6"]`:** 23 rows, all ESZ6, and one warning. This is the quieter version: the customer gets data, just not all of it.
- **preflight** flags "ES" as a FAIL and suggests `ES.FUT` and `ES.c.0`.
- **The four ways to ask:**

  | symbols | stype_in | Instruments | One day of trades |
  |---|---|---|---|
  | ES | raw_symbol | 0 | error 422 |
  | ESZ6 | raw_symbol | 1 | US$1.243950 |
  | ES.c.0 | continuous | 1 | US$1.243950 |
  | ES.FUT | parent | 41 | US$1.254976 |

- `ES.FUT` covered 41 instruments that day: 21 contracts (out to 2031) and 20 calendar spreads.
- Cost of the run: US$0.000228.

## A note for the team

The same request behaves differently depending on the call. `timeseries.get_range` with only unresolvable symbols returns an empty result with two warnings. `metadata.get_cost` for the same request raises `422 symbology_invalid_request: None of the symbols could be resolved`. Customers who miss the warning see an empty DataFrame and assume the data is missing. Two possible fixes:
- name the likely fix in the warning, for example: "Did you mean ES.FUT (stype_in=parent) or ES.c.0 (stype_in=continuous)?"
- or raise the same 422 that `get_cost` does when nothing at all resolves

## Run it

```text
python cases/02-no-data-for-es/run.py
```
