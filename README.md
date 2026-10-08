# Sizing Tutorial — Part 7 of Build Your Own Quant Research System

Position sizing: how much to bet. `sizing.py` with fixed fractional, Kelly (half), and volatility targeting.

**Article:** https://goosos.com/position-sizing-that-survives

## Run it

```bash
pip install -r requirements.txt
python sizing_demo.py
```

## Files

- `sizing.py` — the module (also in [goosos/quant-toolkit](https://github.com/goosos/quant-toolkit))
- `sizing_demo.py` — compares three sizing methods on MA(20,50)
- `backtest.py` — vendored from Part 1 (so the demo runs standalone)
- `article.md` — full tutorial text

## Results (SPY, 2023-10 → 2026-10)

| Method | Return | Sharpe | Max DD |
|---|---|---|---|
| Fixed 100% | 27.21% | 1.03 | -11.49% |
| Fixed 50% | 13.61% | 1.03 | -5.74% |
| Vol-target 15% | 2.58% | 0.94 | -0.31% |

Half-Kelly on this strategy: 30.8%.
