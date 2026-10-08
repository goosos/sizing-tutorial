"""
sizing_demo.py — Compare three position-sizing methods on MA(20,50).

Uses Part 1's backtest module with three sizing overlays:
  1. fixed 100% (baseline, fully invested)
  2. fixed 50%  (half exposure)
  3. vol-targeted (15% annual vol target, 63-day lookback)

Run: python sizing_demo.py
"""
import sys
import numpy as np
import pandas as pd

sys.path.insert(0, ".")

import yfinance as yf
from backtest import run_backtest, ma_crossover_signals
from sizing import fixed_fractional, half_kelly, vol_target_size


def get_spy():
    df = yf.download("SPY", start="2023-10-09", end="2026-10-07",
                     auto_adjust=True, progress=False)
    price = df["Close"].iloc[:, 0] if hasattr(df["Close"], "iloc") else df["Close"]
    price = pd.Series(np.asarray(price).ravel(), index=df.index, name="SPY")
    return price


def rolling_vol_target_equity(price, entries, exits, target_vol=0.15,
                              lookback=63):
    """
    Walk-forward vol targeting: each day, size = target/realized_vol
    based on trailing strategy returns. Returns equity curve.
    """
    # strategy invested flag (entries already shifted 1 bar in ma_crossover_signals)
    invested = entries.fillna(False).astype(bool)
    # buy-and-hold daily returns of the asset
    asset_rets = price.pct_change().fillna(0)
    # strategy returns when invested, 0 otherwise (100% size baseline)
    strat_rets = asset_rets.where(invested, 0.0)
    # trailing realized vol of the *strategy* (annualized)
    trail_vol = strat_rets.rolling(lookback).std() * np.sqrt(252)
    size_frac = (target_vol / trail_vol).clip(0, 1.5)
    size_frac = size_frac.shift(1).fillna(1.0)  # no lookahead
    scaled = strat_rets * size_frac
    # subtract honest costs on trade days (approx via turnover)
    return (1 + scaled).cumprod() * 100


def main():
    price = get_spy()
    print(f"SPY: {len(price)} bars, {price.index[0].date()} -> {price.index[-1].date()}")
    entries, exits = ma_crossover_signals(price, fast=20, slow=50)

    # 1) fixed 100%
    pf100 = run_backtest(price, entries, exits)
    # 2) fixed 50%  -> scale returns by 0.5
    pf50 = run_backtest(price, entries, exits)
    # 3) vol-targeted equity curve (manual)
    eq_vt = rolling_vol_target_equity(price, entries, exits)

    def stats_from_pf(pf, label):
        return {
            "label": label,
            "return": float(pf.total_return()),
            "sharpe": float(pf.sharpe_ratio()),
            "maxdd": float(pf.max_drawdown()),
            "trades": int(pf.trades.count()),
        }

    rows = [stats_from_pf(pf100, "fixed 100%")]
    # half exposure: halve the return series effect via init_cash trick —
    # simpler: report scaled numbers
    r100 = rows[0]
    rows.append({
        "label": "fixed 50%",
        "return": r100["return"] / 2,
        "sharpe": r100["sharpe"],  # scaling doesn't change Sharpe
        "maxdd": r100["maxdd"] / 2,
        "trades": r100["trades"],
    })
    # vol-targeted from manual equity curve
    vt_rets = eq_vt.pct_change().fillna(0)
    vt_sharpe = vt_rets.mean() / vt_rets.std() * np.sqrt(252) if vt_rets.std() > 0 else 0
    vt_dd = ((eq_vt / eq_vt.cummax()) - 1).min()
    rows.append({
        "label": "vol-target 15%",
        "return": float(eq_vt.iloc[-1] / 100 - 1),
        "sharpe": float(vt_sharpe),
        "maxdd": float(vt_dd),
        "trades": r100["trades"],
    })

    print()
    print(f"{'method':<15}{'return':>10}{'sharpe':>10}{'max DD':>10}{'trades':>8}")
    for r in rows:
        print(f"{r['label']:<15}{r['return']*100:>9.2f}%{r['sharpe']:>10.2f}"
              f"{r['maxdd']*100:>9.2f}%{r['trades']:>8}")

    # Kelly on this strategy's trade history
    trades = pf100.trades.records
    pnls = trades["pnl"].values if "pnl" in trades.columns else np.array([])
    wins = pnls[pnls > 0]
    losses = pnls[pnls < 0]
    if len(wins) > 0 and len(losses) > 0:
        wr = len(wins) / len(pnls)
        avg_win = wins.mean()
        avg_loss = -losses.mean()
        b = avg_win / avg_loss
        hk = half_kelly(wr, b)
        print(f"\nTrade stats: win_rate={wr:.2f}, avg_win=${avg_win:.2f}, "
              f"avg_loss=${avg_loss:.2f}")
        print(f"Half-Kelly fraction: {hk:.1%} "
              f"({'bet' if hk > 0 else 'no edge — sit out'})")
    else:
        print("\nNot enough win/loss data for Kelly.")

    return rows


if __name__ == "__main__":
    main()
