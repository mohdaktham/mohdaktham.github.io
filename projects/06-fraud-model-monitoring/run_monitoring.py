"""Monthly monitoring report for a card fraud model, on simulated data.

Development: the model is trained on 2025-01 and 2025-02 and validated out of time
on 2025-03, which becomes the baseline. Production: 2025-04 to 2025-12 are scored
and each month is compared with that baseline.

The report is run as of 2026-01-05. Fraud is confirmed through claims and
chargebacks weeks after the transaction, so performance for November and December
is provisional; stability checks (PSI, CSI) need no labels and are current.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier

from monitoring.metrics import alert_metrics, auc_and_gini, ks_statistic, psi
from simulate import FEATURES, MONTHS, simulate

HERE = Path(__file__).parent
OUT, CHARTS = HERE / "outputs", HERE / "charts"
REPORT_AS_OF = "2026-01"
LABEL_DELAY_MONTHS = 2
TARGET_ALERT_RATE = 0.01
EVENTS = {"2025-06": "online spending shift",
          "2025-08": "distance feed fault",
          "2025-10": "new fraud pattern"}

# Thresholds a monitoring standard would set. PSI bands are the common rule of thumb.
PSI_WATCH, PSI_ACT = 0.10, 0.25
AUC_WATCH, AUC_ACT = 0.03, 0.05
DET_WATCH, DET_ACT = 0.05, 0.10

INK, INK_2, GRID, SURFACE = "#0b0b0b", "#52514e", "#e4e3de", "#fcfcfb"
BLUE, ORANGE = "#2a78d6", "#eb6834"


def model_inputs(df):
    """What the model actually receives: distance as delivered by the feed."""
    X = df[FEATURES].copy()
    X["distance_from_home"] = df["distance_as_received"]
    return X


def labels_mature(month):
    return pd.Period(month, "M") + LABEL_DELAY_MONTHS < pd.Period(REPORT_AS_OF, "M")


def status(row, base):
    level, reasons = 0, []

    def flag(lvl, text):
        nonlocal level
        level = max(level, lvl)
        reasons.append(text)

    if row["score_psi"] > PSI_ACT:
        flag(2, f"score PSI {row['score_psi']:.2f}")
    elif row["score_psi"] > PSI_WATCH:
        flag(1, f"score PSI {row['score_psi']:.2f}")
    if row["top_csi"] > PSI_ACT:
        flag(2, f"CSI on {row['top_feature']} {row['top_csi']:.2f}")
    elif row["top_csi"] > PSI_WATCH:
        flag(1, f"CSI on {row['top_feature']} {row['top_csi']:.2f}")
    if row["labels_mature"]:
        d_auc = base["auc"] - row["auc"]
        d_det = base["detection_rate"] - row["detection_rate"]
        if d_auc > AUC_ACT:
            flag(2, f"AUC down {d_auc:.3f}")
        elif d_auc > AUC_WATCH:
            flag(1, f"AUC down {d_auc:.3f}")
        if d_det > DET_ACT:
            flag(2, f"detection down {100 * d_det:.0f} pts")
        elif d_det > DET_WATCH:
            flag(1, f"detection down {100 * d_det:.0f} pts")
    if level == 0 and not row["labels_mature"]:
        return "pending", "inputs and scores stable; performance waits for labels to mature"
    return ["green", "amber", "red"][level], "; ".join(reasons) or "within thresholds"


def build_report(df, threshold, baseline_scores, baseline_inputs):
    rows = []
    for month in MONTHS[2:]:
        g = df[df["month"] == month]
        X = model_inputs(g)
        auc, gini = auc_and_gini(g["is_fraud"], g["score"])
        csi = {f: psi(baseline_inputs[f], X[f]) for f in FEATURES}
        top = max(csi, key=csi.get)
        rows.append({
            "month": month,
            "transactions": len(g),
            "fraud_rate": g["is_fraud"].mean(),
            "labels_mature": labels_mature(month),
            "auc": auc,
            "gini": gini,
            "ks": ks_statistic(g["is_fraud"], g["score"]),
            **alert_metrics(g["is_fraud"], g["score"], threshold, g["amount"]),
            "score_psi": psi(baseline_scores, g["score"]),
            "top_feature": top,
            "top_csi": csi[top],
            **{f"csi_{f}": v for f, v in csi.items()},
        })
    report = pd.DataFrame(rows)
    base = report.iloc[0]
    flags = [status(r, base) for _, r in report.iterrows()]
    report["status"] = [s for s, _ in flags]
    report["reason"] = [r for _, r in flags]
    report.loc[0, ["status", "reason"]] = ["baseline", "out-of-time validation month"]
    return report


def _style(ax, title):
    ax.set_facecolor(SURFACE)
    ax.set_title(title, loc="left", fontsize=11, color=INK, fontweight="bold")
    ax.grid(axis="y", color=GRID, linewidth=0.8)
    ax.tick_params(colors=INK_2, labelsize=9)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(GRID)


def _events(ax, x_of, ymax):
    for month, label in EVENTS.items():
        x = x_of[month]
        ax.axvline(x, color=INK_2, linewidth=0.8, linestyle=":")
        ax.text(x + 0.08, ymax, label, fontsize=8, color=INK_2, va="top")


def _series(ax, x, y, mature, color, label):
    ax.plot(x, y, color=color, linewidth=2, label=label)
    ax.scatter(x[mature], y[mature], s=36, color=color, zorder=3)
    ax.scatter(x[~mature], y[~mature], s=36, facecolor=SURFACE, edgecolor=color, linewidth=1.5, zorder=3)


def charts(report):
    x = np.arange(len(report))
    x_of = dict(zip(report["month"], x))
    labels = [pd.Period(m, "M").strftime("%b") for m in report["month"]]
    mature = report["labels_mature"].to_numpy()

    fig, axes = plt.subplots(2, 1, figsize=(9, 7), sharex=True, facecolor=SURFACE)
    _style(axes[0], "Ranking power held until the new fraud pattern appeared")
    _series(axes[0], x, report["auc"].to_numpy(), mature, BLUE, "AUC")
    _series(axes[0], x, report["ks"].to_numpy(), mature, ORANGE, "KS")
    axes[0].set_ylim(0, 1.05)
    _events(axes[0], x_of, 1.04)
    axes[0].legend(frameon=False, loc="lower left", fontsize=9)
    _style(axes[1], "Share of fraud caught at the alert cut-off")
    _series(axes[1], x, 100 * report["detection_rate"].to_numpy(), mature, BLUE, "Fraud cases caught (%)")
    _series(axes[1], x, 100 * report["value_detection_rate"].to_numpy(), mature, ORANGE, "Fraud dollars caught (%)")
    axes[1].set_ylim(0, 100)
    _events(axes[1], x_of, 99)
    axes[1].legend(frameon=False, loc="lower left", fontsize=9)
    axes[1].set_xticks(x, labels)
    fig.text(0.01, 0.005, "Hollow points: labels not mature yet (60-day window), provisional.", fontsize=8, color=INK_2)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(CHARTS / "performance.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(9, 7.5), facecolor=SURFACE,
                             gridspec_kw={"height_ratios": [1, 1.3]})
    _style(axes[0], "Score distribution shift (PSI) against the March baseline")
    axes[0].plot(x, report["score_psi"], color=BLUE, linewidth=2, marker="o", markersize=6)
    for level, text in ((PSI_WATCH, "watch 0.10"), (PSI_ACT, "investigate 0.25")):
        axes[0].axhline(level, color=INK_2, linewidth=0.8, linestyle="--")
        axes[0].text(len(x) - 0.6, level, text, fontsize=8, color=INK_2, va="bottom", ha="right")
    axes[0].set_ylim(0, max(0.3, report["score_psi"].max() * 1.15))
    _events(axes[0], x_of, axes[0].get_ylim()[1] * 0.98)
    axes[0].set_xticks(x, labels)
    csi = report[[f"csi_{f}" for f in FEATURES]].to_numpy().T
    ax = axes[1]
    im = ax.imshow(np.minimum(csi, 1.0), aspect="auto", cmap="Blues", vmin=0, vmax=1.0)
    ax.set_title("Input shift by feature (CSI), capped at 1.0 for colour", loc="left",
                 fontsize=11, color=INK, fontweight="bold")
    ax.set_yticks(range(len(FEATURES)), FEATURES, fontsize=9, color=INK_2)
    ax.set_xticks(x, labels, fontsize=9, color=INK_2)
    for i in range(csi.shape[0]):
        for j in range(csi.shape[1]):
            if csi[i, j] >= PSI_WATCH:
                ax.text(j, i, f"{csi[i, j]:.2f}", ha="center", va="center", fontsize=8,
                        color="white" if csi[i, j] > 0.5 else INK)
    for side in ax.spines.values():
        side.set_visible(False)
    fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02).ax.tick_params(labelsize=8, colors=INK_2)
    fig.tight_layout()
    fig.savefig(CHARTS / "stability.png", dpi=150)
    plt.close(fig)

    fig, axes = plt.subplots(2, 1, figsize=(9, 6), sharex=True, facecolor=SURFACE)
    _style(axes[0], "Alert rate (% of transactions flagged)")
    axes[0].plot(x, 100 * report["alert_rate"], color=BLUE, linewidth=2, marker="o", markersize=6)
    axes[0].set_ylim(0, max(2.0, 100 * report["alert_rate"].max() * 1.2))
    _events(axes[0], x_of, axes[0].get_ylim()[1] * 0.98)
    _style(axes[1], "False alarms per fraud caught (the investigators' workload)")
    _series(axes[1], x, report["false_positives_per_fraud"].to_numpy(), mature, BLUE, "False alarms per fraud caught")
    axes[1].set_ylim(0, report["false_positives_per_fraud"].max() * 1.2)
    _events(axes[1], x_of, axes[1].get_ylim()[1] * 0.98)
    axes[1].set_xticks(x, labels)
    fig.tight_layout()
    fig.savefig(CHARTS / "alerts.png", dpi=150)
    plt.close(fig)


def findings(report, threshold, df):
    r = report.set_index("month")
    b = r.loc["2025-03"]
    pct = lambda v: f"{100 * v:.1f}%"
    lines = [
        "FRAUD MODEL MONITORING, SIMULATED DATA: KEY FINDINGS",
        "=" * 52,
        f"Report as of {REPORT_AS_OF}; labels mature after {LABEL_DELAY_MONTHS} months",
        f"Transactions per month: {int(b['transactions']):,}; alert cut-off set for a {pct(TARGET_ALERT_RATE)} alert rate (score >= {threshold:.4f})",
        "",
        "BASELINE (2025-03, out-of-time validation)",
        f"  AUC {b['auc']:.3f}, Gini {b['gini']:.3f}, KS {b['ks']:.3f}",
        f"  fraud cases caught {pct(b['detection_rate'])}, fraud dollars caught {pct(b['value_detection_rate'])}",
        f"  {b['false_positives_per_fraud']:.1f} false alarms per fraud caught",
        "",
    ]
    for month, label in EVENTS.items():
        m = r.loc[month]
        lines += [
            f"{month}  {label.upper()}  status: {m['status']}",
            (f"  score PSI {m['score_psi']:.3f}; largest input shift: {m['top_feature']} (CSI {m['top_csi']:.3f})"
             if m['top_csi'] >= 0.01 else f"  score PSI {m['score_psi']:.3f}; no input moved (largest CSI {m['top_csi']:.3f})"),
            f"  AUC {m['auc']:.3f} (baseline {b['auc']:.3f}); fraud cases caught {pct(m['detection_rate'])} (baseline {pct(b['detection_rate'])})",
            f"  alert rate {pct(m['alert_rate'])}; reasons: {m['reason']}",
            "",
        ]
    new_share = (df[(df.month >= "2025-10") & (df.is_fraud == 1)].fraud_type == "new_pattern").mean()
    lines += [
        f"New-pattern share of fraud from 2025-10: {pct(new_share)}",
        "",
        "MONTH BY MONTH",
        report[["month", "status", "auc", "detection_rate", "alert_rate", "score_psi", "top_feature", "top_csi", "labels_mature"]]
        .to_string(index=False, float_format=lambda v: f"{v:.3f}"),
    ]
    (HERE / "findings.txt").write_text("\n".join(lines) + "\n")


def main():
    OUT.mkdir(exist_ok=True)
    CHARTS.mkdir(exist_ok=True)
    df = simulate(n_per_month=100_000)
    dev = df[df["month"].isin(["2025-01", "2025-02"])]
    model = HistGradientBoostingClassifier(max_iter=300, learning_rate=0.05, max_leaf_nodes=15,
                                           l2_regularization=1.0, random_state=7)
    model.fit(model_inputs(dev), dev["is_fraud"])
    df["score"] = model.predict_proba(model_inputs(df))[:, 1]

    baseline_scores = df.loc[df["month"] == "2025-03", "score"].to_numpy()
    threshold = float(np.quantile(baseline_scores, 1 - TARGET_ALERT_RATE))
    baseline_inputs = model_inputs(df[df["month"].isin(MONTHS[:3])])

    report = build_report(df, threshold, baseline_scores, baseline_inputs)
    report.to_csv(OUT / "monitoring_report.csv", index=False, float_format="%.4f")
    charts(report)
    findings(report, threshold, df)
    print((HERE / "findings.txt").read_text())


if __name__ == "__main__":
    main()
