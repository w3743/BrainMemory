"""
连续强度模型

两个基本力：
  - 自适应衰减：有效衰减率 = decay_rate × (2.0 - R)，越弱忘越快
  - 访问强化：new = R + 0.35 × (1 - R)，渐进逼近 1.0

不再使用 L1/L2/L3 分层——直接用连续强度 R（0.0-1.0）表示记忆质量。
"""

from __future__ import annotations

import math
from datetime import datetime

from .models import Memory, utc_now

# 基础衰减率
DECAY_RATE: float = 0.02  # 每天基础衰减 2%

# 每次被使用的强化增益
REINFORCEMENT_GAIN: float = 0.35

# 默认初始强度
INITIAL_STRENGTH: float = 0.6

# 归档阈值：R 低于此值的记忆自动归档
ARCHIVE_THRESHOLD: float = 0.01


def elapsed_days(since: datetime | None, now: datetime | None = None) -> float:
    """计算自某个时间点以来的天数。"""
    if since is None:
        return 0.0
    now = now or utc_now()
    if since.tzinfo is None:
        since = since.replace(tzinfo=now.tzinfo)
    return max(0.0, (now - since).total_seconds() / 86400.0)


def current_strength(memory: Memory, now: datetime | None = None) -> float:
    """计算记忆当前的强度（自适应衰减后）。

    有效衰减率 = decay_rate × (2.0 - R_at_time)
    越弱的记忆忘得越快，形成"富者愈富"的正反馈。
    """
    days = elapsed_days(memory.last_accessed_at or memory.updated_at or memory.created_at, now)
    if days <= 0:
        return memory.strength

    # 自适应衰减：effective_d = decay_rate × (2 - R)
    # R 高（接近 1.0）→ effective_d ≈ decay_rate（慢忘）
    # R 低（接近 0.0）→ effective_d ≈ 2 × decay_rate（快忘）
    s0 = memory.strength
    d = memory.decay_rate
    # 解微分方程 dR/dt = -d * (2-R) * R 的近似：分段数值积分
    # 简化为：effective_d = d * (2 - average_R)
    # 使用中点近似
    # 精确解：R(t) = 2 / (1 + (2/s0 - 1) * exp(2*d*t))
    # 推导：dR/dt = -d * (2-R) * R，分离变量 → 积分
    if s0 >= 1.0:
        return 1.0
    if s0 <= 0.0:
        return 0.0

    coeff = (2.0 / s0) - 1.0
    R = 2.0 / (1.0 + coeff * math.exp(2.0 * d * days))
    return max(0.0, min(1.0, R))


def reinforce(memory: Memory) -> float:
    """访问强化：从当前衰减强度 R 向 1.0 移动固定比例。

    公式：new = R + REINFORCEMENT_GAIN × (1 - R)
    每次访问将剩余距离缩短 35%，渐进逼近 1.0。
    同时减小 decay_rate，使频繁访问的记忆遗忘更慢。
    """
    R = current_strength(memory)

    new_strength = R + REINFORCEMENT_GAIN * (1.0 - R)
    new_strength = max(0.0, min(1.0, new_strength))

    # Stability 对数增长：频繁访问的记忆遗忘更慢
    if memory.decay_rate > 0:
        old_S = math.log(2) / memory.decay_rate
    else:
        old_S = 30.0
    new_S = old_S * (1.0 + REINFORCEMENT_GAIN)
    memory.decay_rate = max(0.001, min(0.3, math.log(2) / new_S))

    return new_strength
