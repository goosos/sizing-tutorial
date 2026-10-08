"""
sizing.py — Part 7 of "Build Your Own Quant Research System".

Position sizing: how much to bet on each trade. The least glamorous
part of quant research, and the one that determines whether you
survive long enough for your edge to matter.

Three approaches:
  fixed_fractional() — bet X% of equity per trade. Simple, robust.
  kelly_fraction()   — the theoretically optimal growth bet (use half).
  vol_target_size()   — size so portfolio volatility hits a target.

Tutorial: https://goosos.com/position-sizing-that-survives
Code: https://github.com/goosos/sizing-tutorial
"""

import numpy as np
import pandas as pd


def fixed_fractional(equity, fraction):
    """Position size as a fixed fraction of current equity."""
    if not 0 < fraction <= 1:
        raise ValueError(f"fraction must be in (0, 1], got {fraction}")
    return equity * fraction


def kelly_fraction(win_prob, win_loss_ratio):
    """
    Kelly-optimal fraction: f* = p - (1-p)/b.

    Maximizes long-run log growth. Brutal drawdowns in practice —
    use half_kelly() instead. Negative means no edge: don't bet.
    """
    if not 0 < win_prob < 1:
        raise ValueError(f"win_prob must be in (0, 1), got {win_prob}")
    if win_loss_ratio <= 0:
        raise ValueError(f"win_loss_ratio must be > 0, got {win_loss_ratio}")
    return win_prob - (1 - win_prob) / win_loss_ratio


def half_kelly(win_prob, win_loss_ratio):
    """
    Half-Kelly: ~75% of full-Kelly growth, ~50% less volatility.
    Floored at 0 (never bet negative edge).
    """
    return max(0.0, 0.5 * kelly_fraction(win_prob, win_loss_ratio))


def vol_target_size(equity, returns, target_vol=0.15, lookback=63,
                    min_size=0.0, max_size=1.0):
    """
    Size so portfolio volatility hits target_vol (annualized).

    size = target_vol / realized_vol, clipped to [min_size, max_size].
    Choppy markets -> smaller size. Calm markets -> larger size.
    """
    if len(returns) < 2:
        raise ValueError("need at least 2 return observations")
    recent = returns.iloc[-lookback:] if len(returns) > lookback else returns
    realized = recent.std() * np.sqrt(252)
    if not np.isfinite(realized) or realized <= 0:
        frac = max_size
    else:
        frac = target_vol / realized
    return equity * float(np.clip(frac, min_size, max_size))
