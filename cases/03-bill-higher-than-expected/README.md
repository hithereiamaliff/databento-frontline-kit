# 03. "My bill was higher than I expected"

**Kind:** billing question; works as documented.

## The question

> I pulled one day of ES order-book data expecting a few cents and it came to a few dollars. My estimate was also higher than what I actually downloaded. How does pricing work, and how do I avoid surprises?

## The reply I'd send

> Hi! Three things decide what a request costs.
>
> 1. **The schema.** One day of ES (23 November) is estimated at US$0.0002 as hourly bars, US$1.24 as trades and US$4.47 as `mbp-10`. Order-book schemas carry many more records.
> 2. **How many instruments a symbol covers.** For ES, every contract and spread (`ES.FUT`) adds little: one day of trades went from US$1.24 to US$1.25. Crude oil is different: CL's full order book (`CL.FUT`, `mbo`) was US$3.57, against US$0.54 for the front month.
> 3. **The window.** Estimates round up to 10-minute boundaries, so 14:00 to 14:15 is estimated like 14:00 to 14:20. That's why your estimate came out above what was actually sent.
>
> You can price any request before downloading it, for free:
>
> ```python
> client.metadata.get_cost(
>     dataset="GLBX.MDP3", symbols=["ES.c.0"], stype_in="continuous",
>     schema="trades", start="2026-11-23", end="2026-11-24",
> )
> ```
>
> Two more tips:
> - **Cap your spending.** In the portal, go to Billing and choose Manage under usage-based access, then set a monthly limit. Historical requests stop once you reach it.
> - **Use a batch job for data you'll fetch more than once.** Streaming bills every download, while a batch job bills once and lets you download the files again for 30 days.
>
> The file format doesn't change the price: billing is on the uncompressed binary size, so CSV and JSON cost the same as DBN.

## What the run showed

From [transcript.md](transcript.md), recorded 26 Nov 2026. Every figure except the last one is an estimate from `metadata.get_cost`, which downloads nothing:

- **By schema** (ES.c.0, one day):

  | Schema | Records | Estimate |
  |---|---|---|
  | ohlcv-1h | 23 | US$0.000228 |
  | ohlcv-1m | 1,380 | US$0.005038 |
  | trades | 993,810 | US$1.243950 |
  | mbp-1 | 20,634,389 | US$2.767287 |
  | mbo | 31,247,145 | US$2.933398 |
  | mbp-10 | 26,109,638 | US$4.474235 |

- **Front month against every contract and spread:**
  - ES trades: +1%
  - ES `mbo`: +12%
  - CL `mbo`: 6.6 times as much (US$0.539804 against US$3.572203)

  My first guess, that a parent symbol always multiplies the cost, was wrong for ES. It depends on the product.
- **10-minute boundaries:** 14:00 to 14:15 was estimated at 52,161 records, the same as 14:00 to 14:20.
- **Estimate against what was sent:** the 14:00 to 14:15 slice was downloaded. 43,714 records came back (2,098,272 bytes), so the estimate was 19% too high, as the docs warn. If billing follows what was sent, as the pricing FAQ says for streaming, that's about US$0.0547, not the estimated US$0.0653. I worked that out; it isn't read from an invoice.
- Cost of the run: one download of about US$0.05. Everything else is a free estimate.

## Run it

```text
python cases/03-bill-higher-than-expected/run.py
```
