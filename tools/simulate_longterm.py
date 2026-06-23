"""
长期记忆模拟实验 + 可视化图表（纯 R 值，无分层）

模拟一个开发者在 30 天内的记忆演化，生成：
  1. 强度曲线图（7 条记忆的 R 随时间变化）
  2. 强度热力图（每格标注 R 值）
"""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np

from membrain.engine import CSMEngine
from membrain.strength import current_strength

# ── 场景定义 ────────────────────────────────────────────────────
SCENARIOS = [
    ("tech_stack", "Hi-freq (22x)", "#1a9641",
     [1,2,3,4,5,6,7,9,10,12,14,17,18,19,20,21,24,25,26,27,28,29]),
    ("user_pref", "Personal (6x)", "#377eb8",
     [1,2,8,14,22,28]),
    ("code_review", "Spaced (5x)", "#ff7f00",
     [1,3,7,15,26]),
    ("env_setup", "Moderate (4x)", "#4daf4a",
     [1,5,11,23]),
    ("bug_note", "Low-freq (2x)", "#984ea3",
     [3,19]),
    ("temp_task", "One-time (1x)", "#a65628",
     [1]),
    ("noise", "Never (0x)", "#999999",
     []),
]


def simulate_and_plot(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    db_path = output_dir / "sim_output.db"
    if db_path.exists():
        db_path.unlink()

    engine = CSMEngine(db_path)
    memory_ids: dict[str, int] = {}
    contents = {
        "tech_stack": "bun install + pytest",
        "user_pref": "Simplified Chinese replies",
        "code_review": "Code review required",
        "env_setup": "Python py -3.11 config",
        "bug_note": "SQLite WAL busy_timeout",
        "temp_task": "Temp login test@example",
        "noise": "Friday standup Room B",
    }

    # ── Day 0: 创建所有记忆 ─────────────────────────────────
    now = datetime(2026, 6, 1, 9, 0, tzinfo=timezone.utc)
    for mem_id, mem_type, color, access_days in SCENARIOS:
        m = engine.add_memory(contents[mem_id], project_id="sim", tags=f"type:{mem_id}")
        memory_ids[mem_id] = m.id or 0
        iso = now.isoformat()
        engine.store.conn.execute(
            "UPDATE memories SET created_at=?, updated_at=?, last_accessed_at=? WHERE id=?",
            (iso, iso, iso, m.id),
        )
        engine.store.conn.commit()

    # ── Track daily data ─────────────────────────────────────
    days_list = list(range(0, 31))
    strengths_by_mem: dict[str, list[float]] = {m_id: [] for m_id, _, _, _ in SCENARIOS}
    for mem_id, _, _, _ in SCENARIOS:
        strengths_by_mem[mem_id].append(0.6)

    for day in range(1, 31):
        now += timedelta(days=1)

        for mem_id, mem_type, color, access_days in SCENARIOS:
            if day in access_days:
                mid = memory_ids[mem_id]
                results = engine.search(contents[mem_id][:30], project_id="sim", limit=5)
                for r in results:
                    if r.memory.id == mid:
                        engine.reinforce_used(mid)
                        iso = now.isoformat()
                        engine.store.conn.execute(
                            "UPDATE memories SET last_accessed_at=? WHERE id=?", (iso, mid)
                        )
                        engine.store.conn.commit()
                        break

        all_mems = engine.store.list_all()
        for mem_id, _, _, _ in SCENARIOS:
            mid = memory_ids[mem_id]
            mem = next((m for m in all_mems if m.id == mid), None)
            R = current_strength(mem, now=now) if mem else 0.0
            strengths_by_mem[mem_id].append(R)

    engine.close()
    db_path.unlink()

    # ════════════════════════════════════════════════════════════
    # Chart 1: Strength curves
    # ════════════════════════════════════════════════════════════
    fig, ax = plt.subplots(figsize=(12, 5))
    for mem_id, mem_type, color, _ in SCENARIOS:
        ax.plot(days_list, strengths_by_mem[mem_id],
                color=color, linewidth=2.2, label=mem_type, alpha=0.9)

    # Gradient background for strength zones
    ax.axhspan(0.7, 1.0, alpha=0.05, color="#1a9641")
    ax.axhspan(0.3, 0.7, alpha=0.03, color="#ff7f00")
    ax.axhspan(0.0, 0.3, alpha=0.03, color="#999999")

    ax.set_xlabel("Day", fontsize=12)
    ax.set_ylabel("Memory Strength R", fontsize=12)
    ax.set_title("30-Day Memory Strength Evolution (Adaptive Decay)", fontsize=14, fontweight="bold")
    ax.set_xlim(0, 30)
    ax.set_ylim(0, 1.05)
    ax.legend(loc="center left", bbox_to_anchor=(1.01, 0.5), fontsize=9)
    ax.grid(True, alpha=0.3)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
    fig.tight_layout()
    fig.savefig(output_dir / "strength_curves.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # ════════════════════════════════════════════════════════════
    # Chart 2: Heatmap
    # ════════════════════════════════════════════════════════════
    mem_labels = [m_type for _, m_type, _, _ in SCENARIOS]
    heatmap_data = np.array([strengths_by_mem[m_id] for m_id, _, _, _ in SCENARIOS])

    fig, ax = plt.subplots(figsize=(14, 4.5))
    im = ax.imshow(heatmap_data, aspect="auto", cmap="RdYlGn", vmin=0.0, vmax=1.0,
                   extent=[0, 30, len(mem_labels) - 0.5, -0.5])

    ax.set_yticks(range(len(mem_labels)))
    ax.set_yticklabels(mem_labels, fontsize=9)
    ax.set_xlabel("Day", fontsize=12)
    ax.set_title("Memory Strength Heatmap (Adaptive Decay: weaker = faster forget)", fontsize=13, fontweight="bold")

    for i in range(len(mem_labels)):
        for day in [0, 7, 14, 21, 30]:
            val = heatmap_data[i, day]
            color = "white" if val < 0.5 else "black"
            ax.text(day, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=6.5, color=color, fontweight="bold")

    cbar = fig.colorbar(im, ax=ax, shrink=0.85)
    cbar.set_label("Strength R", fontsize=11)
    ax.xaxis.set_major_locator(mticker.MultipleLocator(5))
    fig.tight_layout()
    fig.savefig(output_dir / "strength_heatmap.png", dpi=200, bbox_inches="tight")
    plt.close(fig)

    # ── Summary ─────────────────────────────────────────────
    print("Charts saved to:", output_dir)
    print("  strength_curves.png  — 7 curves over 30 days")
    print("  strength_heatmap.png — color-coded strength grid")
    print("\nFinal state (Day 30):")
    for mem_id, mem_type, color, access_days in SCENARIOS:
        R = strengths_by_mem[mem_id][-1]
        print(f"  {mem_id:15s} [{mem_type:18s}]  R={R:.3f}  accesses={len(access_days)}")


if __name__ == "__main__":
    out = Path(__file__).resolve().parent / "sim_charts"
    simulate_and_plot(out)
