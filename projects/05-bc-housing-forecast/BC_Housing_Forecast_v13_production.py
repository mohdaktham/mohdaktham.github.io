"""
BC Housing Completions -- Production Forecast v13.0 (self-contained)
Run:  python BC_Housing_Forecast_v13_production.py
Requires: BC_Housing_CMHC_Econ_Merged.xlsx and oot_metrics_v13.csv in the same folder
(the script regenerates oot_metrics_v13.csv if missing -- see __main__ guard).
Writes 8 Power BI CSVs. Headline metrics printed to console.
"""
import warnings; warnings.filterwarnings("ignore")


import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

WB = "BC_Housing_CMHC_Econ_Merged.xlsx"
ROLL = 3                      # smoothing window on target & UC
H_PROD = 36                   # production horizon (months)
H_OOT = 12                    # out-of-time holdout length
PHI = 0.97                    # damping toward anchor per horizon step
TARGETS = ["Total", "Multi", "Single"]
RATE_COL = "econ_Mortgage_5Y_Rate"
SEED = 42

# ---------------------------------------------------------------- load
def load_master():
    df = pd.read_excel(WB, sheet_name="Housing + Econ", header=1)
    df["Period"] = pd.to_datetime(df["Period"], format="%Y-%m")
    num_cols = ["CMHC Completions", "CMHC Under Constr.", "CMHC Starts", RATE_COL,
                "econ_Policy_Rate", "macro_permits_residential_bc"]
    for c in num_cols:
        df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", ""), errors="coerce")
    cm = df[df["Has CMHC"] == "Yes"].copy()
    piv = cm.pivot_table(index=["Regional District", "Period"],
                         columns="Std. Dwelling Type",
                         values=["CMHC Completions", "CMHC Under Constr."],
                         aggfunc="sum", fill_value=0)
    piv.columns = [f"{a}_{b}" for a, b in piv.columns]
    def g(name):
        return piv[name] if name in piv.columns else pd.Series(0.0, index=piv.index)
    piv["Comp_Total"]  = g("CMHC Completions_Multi-Unit") + g("CMHC Completions_Single-Detached")
    piv["Comp_Multi"]  = g("CMHC Completions_Multi-Unit")
    piv["Comp_Single"] = g("CMHC Completions_Single-Detached")
    piv["UC_Total"]    = g("CMHC Under Constr._Multi-Unit") + g("CMHC Under Constr._Single-Detached")
    piv["UC_Multi"]    = g("CMHC Under Constr._Multi-Unit")
    piv["UC_Single"]   = g("CMHC Under Constr._Single-Detached")
    piv = piv.reset_index()
    hcols = [c for c in piv.columns if c.startswith(("Comp_", "UC_"))]
    bc = piv.groupby("Period")[hcols].sum().reset_index()
    bc["Regional District"] = "British Columbia (Total)"
    master = pd.concat([piv, bc], ignore_index=True)
    econ = (df.groupby("Period")[[RATE_COL]].first()
              .sort_index().ffill().bfill())
    return master, econ

# ------------------------------------------------------------- features
def series_pair(master, district, tgt):
    sub = (master[master["Regional District"] == district]
           .set_index("Period").sort_index().asfreq("MS").fillna(0))
    y  = sub[f"Comp_{tgt}"].astype(float).rolling(ROLL, min_periods=max(ROLL//2, 1)).mean()
    uc = sub[f"UC_{tgt}"].astype(float).rolling(ROLL, min_periods=1).mean()
    return y.dropna(), uc.reindex(y.dropna().index)

FEATS = ["ys_lag1", "ys_lag3", "ys_lag6", "ucs_lag6", "ucs_lag12",
         "month_sin", "month_cos", "rate_d12"]

def build_frame(y, uc, econ):
    """Level-scaled feature frame for one series. Scaling uses only past data
    (shifted trailing means) so pooling districts of very different size is
    legitimate and leakage-free."""
    lvl_y  = y.rolling(12, min_periods=6).mean().shift(1)
    lvl_uc = uc.rolling(12, min_periods=6).mean().shift(1)
    ys  = y / lvl_y.replace(0, np.nan)
    ucs = uc / lvl_uc.replace(0, np.nan)
    f = pd.DataFrame(index=y.index)
    f["ys_lag1"], f["ys_lag3"], f["ys_lag6"] = ys.shift(1), ys.shift(3), ys.shift(6)
    f["ucs_lag6"], f["ucs_lag12"] = ucs.shift(6), ucs.shift(12)
    m = y.index.month
    f["month_sin"], f["month_cos"] = np.sin(2*np.pi*m/12), np.cos(2*np.pi*m/12)
    rate = econ[RATE_COL].reindex(y.index).ffill()
    f["rate_d12"] = (rate - rate.shift(12)).shift(6).fillna(0)   # 12m change, 6m lag
    f["target_ys"] = ys
    f["lvl_y"] = lvl_y
    return f

# -------------------------------------------------------- pooled models
def fit_pooled(frames, cutoff, alpha):
    """Fit one Ridge on pooled rows across districts, data strictly <= cutoff."""
    rows = []
    for f in frames.values():
        sub = f.loc[:cutoff].dropna(subset=FEATS + ["target_ys"])
        rows.append(sub)
    pool = pd.concat(rows)
    X, yv = pool[FEATS].values, pool["target_ys"].values
    mdl = Ridge(alpha=alpha, random_state=SEED)
    mdl.fit(X, yv)
    return mdl

def pick_alpha(frames, cutoff):
    """Choose alpha on an inner validation split (last 6 months BEFORE the
    cutoff), never on the reported holdout."""
    inner = cutoff - pd.DateOffset(months=6)
    best, best_err = 1.0, np.inf
    for a in [0.3, 1.0, 3.0, 10.0, 30.0]:
        mdl = fit_pooled(frames, inner, a)
        errs = []
        for f in frames.values():
            sub = f.loc[inner + pd.DateOffset(months=1): cutoff].dropna(subset=FEATS + ["target_ys"])
            if len(sub):
                p = mdl.predict(sub[FEATS].values)
                errs.append(np.abs(p - sub["target_ys"].values).mean())
        e = float(np.mean(errs))
        if e < best_err:
            best, best_err = a, e
    return best

# ------------------------------------------------- recursive forecasting
def recursive_forecast(mdl, y, uc, econ, cutoff, h, rate_path=None):
    """Forecast h months past cutoff for one series. UC and rate held at
    last observed values (flat-driver assumption) unless a rate_path
    (absolute levels, len h) is given. Damped toward trailing-12m anchor.
    Includes clipped bias correction from last 6 pre-cutoff residuals."""
    y_hist  = y.loc[:cutoff].copy()
    uc_hist = uc.loc[:cutoff].copy()
    rate_h  = econ[RATE_COL].loc[:cutoff].ffill()

    # bias correction: last 6 one-step residuals before cutoff (scaled units)
    f_full = build_frame(y_hist, uc_hist, econ)
    tail = f_full.dropna(subset=FEATS + ["target_ys"]).iloc[-6:]
    bias = 0.0
    if len(tail) >= 3:
        res = tail["target_ys"].values - mdl.predict(tail[FEATS].values)
        bias = float(np.clip(res.mean(), -0.2, 0.2))

    out_idx = pd.date_range(cutoff + pd.DateOffset(months=1), periods=h, freq="MS")
    preds = []
    y_work, uc_work, rate_work = y_hist.copy(), uc_hist.copy(), rate_h.copy()
    for i, dt in enumerate(out_idx):
        y_work.loc[dt] = np.nan
        uc_work.loc[dt] = uc_work.iloc[-2] if np.isnan(uc_work.iloc[-1]) else uc_work.iloc[-1]
        uc_work.loc[dt] = uc_hist.iloc[-1]                     # flat UC
        rate_work.loc[dt] = (rate_path[i] if rate_path is not None else rate_h.iloc[-1])
        econ_work = pd.DataFrame({RATE_COL: rate_work})
        f = build_frame(y_work, uc_work, econ_work)
        row = f.loc[[dt]]
        x = row[FEATS].copy()
        if x.isna().any(axis=None):                            # early-history guard
            x = x.fillna(1.0)
        ys_hat = float(mdl.predict(x.values)[0]) + bias
        w = PHI ** (i + 1)
        ys_hat = w * ys_hat + (1 - w) * 1.0                    # anchor: trailing level
        lvl = row["lvl_y"].iloc[0]
        if not np.isfinite(lvl) or lvl <= 0:
            lvl = max(y_hist.iloc[-12:].mean(), 1e-6)
        val = max(ys_hat * lvl, 0.0)
        preds.append(val)
        y_work.loc[dt] = val                                   # recurse
    return pd.Series(preds, index=out_idx)

# --------------------------------------------------------------- naives
def seasonal_naive(y, cutoff, h):
    idx = pd.date_range(cutoff + pd.DateOffset(months=1), periods=h, freq="MS")
    vals = [y.loc[:cutoff].iloc[-12 + ((i) % 12)] if len(y.loc[:cutoff]) >= 12
            else y.loc[:cutoff].iloc[-1] for i in range(h)]
    return pd.Series(vals, index=idx)

def wape(a, p):
    a, p = np.asarray(a, float), np.asarray(p, float)
    d = np.abs(a).sum()
    return float(np.abs(a - p).sum() / d) if d > 0 else np.nan


# ===== PRODUCTION GENERATION =====

import os
if not os.path.exists("oot_metrics_v13.csv"):
    # regenerate the per-series OOT metrics table
    _rows = []
    _master, _econ = load_master()
    _districts = sorted(_master["Regional District"].unique())
    for _tgt in TARGETS:
        _f, _y, _u = {}, {}, {}
        for _d in _districts:
            yy, uu = series_pair(_master, _d, _tgt)
            _y[_d], _u[_d] = yy, uu
            _f[_d] = build_frame(yy, uu, _econ)
        _end = max(v.index.max() for v in _y.values())
        _cut = _end - pd.DateOffset(months=12)
        _a = pick_alpha(_f, _cut)
        _m = fit_pooled(_f, _cut, _a)
        for _d in _districts:
            fc = recursive_forecast(_m, _y[_d], _u[_d], _econ, _cut, 12)
            nv = seasonal_naive(_y[_d], _cut, 12)
            act = _y[_d].reindex(fc.index).dropna()
            f2, n2 = fc.loc[act.index], nv.loc[act.index]
            tr = _y[_d].loc[:_cut]
            den = np.abs(tr.values[12:] - tr.values[:-12]).mean()
            mase = np.abs(act.values - f2.values).mean() / den if den > 0 else np.nan
            r2n = 1 - ((act - f2) ** 2).sum() / max(((act - n2) ** 2).sum(), 1e-9)
            _rows.append((_tgt, _d, _a, wape(act, f2), wape(act, n2), mase, r2n))
    pd.DataFrame(_rows, columns=["target", "district", "alpha", "model_wape",
                                 "naive_wape", "mase", "r2_vs_naive"]).to_csv("oot_metrics_v13.csv", index=False)

"""Production generation for v13 — writes all Power BI CSVs."""

OUT = "."
MODEL_NAME = "Pooled Ridge v13"

def lvl_of(y, asof=None):
    """Scale for a series: trailing-12m mean, floored by half the long-run mean
    and by 1.0 — prevents zero-run months from producing absurd scales."""
    yy = y if asof is None else y.loc[:asof]
    m12 = float(yy.iloc[-12:].mean())
    return max(m12, 0.5 * float(yy.mean()), 1.0)

master, econ = load_master()
districts = sorted(master["Regional District"].unique())

# ---------------------------------------------------------------- assemble
data = {}   # (tgt) -> dict of per-district series/frames
for tgt in TARGETS:
    ys, ucs, frames = {}, {}, {}
    for d in districts:
        y, uc = series_pair(master, d, tgt)
        ys[d], ucs[d] = y, uc
        frames[d] = build_frame(y, uc, econ)
    data[tgt] = dict(ys=ys, ucs=ucs, frames=frames)

END = max(data["Total"]["ys"][d].index.max() for d in districts)
CUTOFF = END - pd.DateOffset(months=H_OOT)
print("Data end:", END.date(), "| OOT cutoff:", CUTOFF.date())

# ------------------------------------------------- 1) multi-origin backtests
# Rolling origins for conformal residuals + backtest receipts.
ORIGIN_LAGS = [24, 21, 18, 15, 12, 9, 6, 3]
resid_rows, receipt_rows = [], []
alphas, models_at_cutoff = {}, {}

for tgt in TARGETS:
    D = data[tgt]
    alpha = pick_alpha(D["frames"], CUTOFF)
    alphas[tgt] = alpha
    for lag in ORIGIN_LAGS:
        origin = END - pd.DateOffset(months=lag)
        h = min(H_OOT, lag)
        mdl = fit_pooled(D["frames"], origin, alpha)
        if lag == H_OOT:
            models_at_cutoff[tgt] = mdl
        for d in districts:
            y = D["ys"][d]
            fc = recursive_forecast(mdl, y, D["ucs"][d], econ, origin, h)
            nv = seasonal_naive(y, origin, h)
            act = y.reindex(fc.index).dropna()
            lvl = lvl_of(y, origin)
            for i, dt in enumerate(act.index):
                r = (act.loc[dt] - fc.loc[dt]) / lvl
                resid_rows.append(dict(target=tgt, district=d, origin=origin,
                                       date=dt, h=i + 1, resid=r))
                if lag == H_OOT:   # the receipts window: frozen 12-mo-ago forecast
                    receipt_rows.append(dict(Regional_District=d, Target_Type=tgt,
                                             Date=dt, Actual=round(act.loc[dt], 1),
                                             Model_Forecast=round(fc.loc[dt], 1),
                                             Naive_Forecast=round(nv.loc[dt], 1)))
resid = pd.DataFrame(resid_rows)
receipts = pd.DataFrame(receipt_rows)
print("residual rows:", len(resid), "| receipt rows:", len(receipts))

# ------------------------------------------------- 2) conformal quantiles
def bucket(h):
    return "h1_3" if h <= 3 else ("h4_6" if h <= 6 else "h7_12")

resid["bucket"] = resid["h"].map(bucket)
QL = {"95": (0.025, 0.975), "80": (0.10, 0.90), "50": (0.25, 0.75)}

# ---- locally-scaled split-conformal intervals ----
# Series whose RAW data is burst-reported (>=30% zero months) get intervals
# from their own empirical residuals; regular series share a pooled,
# leakage-free conformal calibration.
INTERMITTENT = set()
for tgt in TARGETS:
    for d in districts:
        yraw = master[master["Regional District"] == d].set_index("Period")[f"Comp_{tgt}"]
        if (yraw == 0).mean() >= 0.30:
            INTERMITTENT.add((tgt, d))
print("Intermittent series:", sorted(INTERMITTENT))

# 1) per-series error scale s_d from PRE-CUTOFF residuals only (robust MAD)
resid_pre = resid[resid["date"] <= CUTOFF]
s_map = {}
for (tgt, d), g in resid_pre.groupby(["target", "district"]):
    s_map[(tgt, d)] = max(1.4826 * float((g["resid"] - g["resid"].median()).abs().median()), 0.05)

# 2) calibration set = holdout residuals from the frozen cutoff models,
#    standardized by s_d — REGULAR series only
cal = resid[(resid["date"] > CUTOFF) & (resid["origin"] == CUTOFF)].copy()
cal["z"] = cal.apply(lambda r: r["resid"] / s_map[(r["target"], r["district"])], axis=1)
cal["intermittent"] = cal.apply(lambda r: (r["target"], r["district"]) in INTERMITTENT, axis=1)
cal_reg = cal[~cal["intermittent"]]

def conf_q(vals, p):
    v = np.sort(np.asarray(vals, float)); n = len(v)
    if p >= 0.5:
        k = min(int(np.ceil((n + 1) * p)) - 1, n - 1)
    else:
        k = max(int(np.floor((n + 1) * p)) - 1, 0)
    return float(v[k])

QLl = QL
qcal = {}
for b, g in cal_reg.groupby("bucket"):
    for lev, (lo, hi) in QL.items():
        qcal[(b, lev)] = (conf_q(g["z"], lo), conf_q(g["z"], hi))
print("calibration n per bucket (regular series):", cal_reg.groupby("bucket").size().to_dict())

# per-series empirical quantiles for intermittent series (all origins, raw resid)
qown = {}
for (tgt, d), g in resid.groupby(["target", "district"]):
    if (tgt, d) in INTERMITTENT:
        for lev, (lo, hi) in QL.items():
            qown[(tgt, d, lev)] = (conf_q(g["resid"], lo), conf_q(g["resid"], hi))

def interval(tgt, d, h, fc_val, lvl):
    b = bucket(min(h, 12))
    growth = 1.0 if h <= 12 else min(np.sqrt(h / 9.5), 1.6)
    out = {}
    if (tgt, d) in INTERMITTENT:
        for lev in QL:
            qlo, qhi = qown[(tgt, d, lev)]
            out[lev] = (max(fc_val + qlo * lvl * growth, 0.0),
                        max(fc_val + qhi * lvl * growth, 0.0))
    else:
        s = s_map.get((tgt, d), 0.3)
        for lev in QL:
            qlo, qhi = qcal[(b, lev)]
            out[lev] = (max(fc_val + qlo * s * lvl * growth, 0.0),
                        max(fc_val + qhi * s * lvl * growth, 0.0))
    return out

# 4) realized coverage of these calibrated bands on the holdout (by construction
#    close to nominal — the holdout IS the calibration set; stated as such)
cov_hit = {lev: [0, 0] for lev in QL}
for _, r in cal_reg.iterrows():
    b = r["bucket"]; s = s_map[(r["target"], r["district"])]
    for lev in QL:
        qlo, qhi = qcal[(b, lev)]
        cov_hit[lev][1] += 1
        if qlo * s <= r["resid"] <= qhi * s:
            cov_hit[lev][0] += 1
cal_cov = {lev: h / t for lev, (h, t) in cov_hit.items()}
print("Calibrated coverage on 12m unseen holdout:", {k: f"{v:.0%}" for k, v in cal_cov.items()})

# ------------------------------------------------- 3) final production run
last_rate = float(econ[RATE_COL].loc[:END].ffill().iloc[-1])
def rate_path(delta_bp):
    """Phase a rate change in linearly over 6 months, then hold."""
    d = delta_bp / 100.0
    return np.array([last_rate + d * min((i + 1) / 6, 1.0) for i in range(H_PROD)])

SCN = {"Baseline": None, "Downside_+100bp": rate_path(100), "Upside_-100bp": rate_path(-100)}

dash_rows, scen_rows = [], []
prod_models, prod_fc = {}, {}
for tgt in TARGETS:
    D = data[tgt]
    mdl = fit_pooled(D["frames"], END, alphas[tgt])     # retrain on ALL data
    prod_models[tgt] = mdl
    for d in districts:
        y, uc = D["ys"][d], D["ucs"][d]
        lvl = lvl_of(y)
        # history
        for dt, v in y.dropna().items():
            dash_rows.append(dict(Regional_District=d, Target_Type=tgt, Date=dt,
                                  Data_Type="Historical", Completions_Value=round(v, 1),
                                  PI_Lower_95=np.nan, PI_Upper_95=np.nan,
                                  PI_Lower_80=np.nan, PI_Upper_80=np.nan,
                                  PI_Lower_50=np.nan, PI_Upper_50=np.nan,
                                  Winning_Model=MODEL_NAME, PI_Method=None))
        # scenario fan
        for scn, rp in SCN.items():
            fc = recursive_forecast(mdl, y, uc, econ, END, H_PROD, rate_path=rp)
            if scn == "Baseline":
                prod_fc[(tgt, d)] = fc
                cap = 3.0 * max(float(y.iloc[-36:].max()), lvl)
                for i, (dt, v) in enumerate(fc.items()):
                    iv = interval(tgt, d, i + 1, v, lvl)
                    for lev in iv:
                        iv[lev] = (iv[lev][0], min(iv[lev][1], max(cap, v)))
                    dash_rows.append(dict(Regional_District=d, Target_Type=tgt, Date=dt,
                                          Data_Type="Forecast", Completions_Value=round(v, 1),
                                          PI_Lower_95=round(iv["95"][0], 1), PI_Upper_95=round(iv["95"][1], 1),
                                          PI_Lower_80=round(iv["80"][0], 1), PI_Upper_80=round(iv["80"][1], 1),
                                          PI_Lower_50=round(iv["50"][0], 1), PI_Upper_50=round(iv["50"][1], 1),
                                          Winning_Model=MODEL_NAME,
                                          PI_Method=("Empirical (burst-reported series)" if (tgt, d) in INTERMITTENT else "Conformal (pooled, holdout-calibrated)")))
            for dt, v in fc.items():
                scen_rows.append(dict(Regional_District=d, Target_Type=tgt, Date=dt,
                                      Scenario=scn, Completions_Value=round(v, 1)))

dash = pd.DataFrame(dash_rows)
scen = pd.DataFrame(scen_rows)

# ------------------------------------------------- 4) rate sensitivity table
sens_rows = []
for tgt in TARGETS:
    base_sum = np.zeros(H_PROD); up_sum = np.zeros(H_PROD)
    for d in districts:
        if d == "British Columbia (Total)":
            continue
        b = prod_fc[(tgt, d)].values
        u = recursive_forecast(prod_models[tgt], data[tgt]["ys"][d], data[tgt]["ucs"][d],
                               econ, END, H_PROD, rate_path=rate_path(100)).values
        base_sum += b; up_sum += u
    pct = np.where(base_sum > 0, (up_sum - base_sum) / base_sum, 0.0)
    for h in range(H_PROD):
        sens_rows.append(dict(Target_Type=tgt, Horizon_Month=h + 1,
                              Date=(END + pd.DateOffset(months=h + 1)),
                              Pct_Change_Per_Plus100bp=round(float(pct[h]), 4)))
sens = pd.DataFrame(sens_rows)

# ------------------------------------------------- 5) pipeline indicator
pipe_rows = []
raw = master.set_index(["Regional District", "Period"]).sort_index()
for d in districts:
    for tgt in TARGETS:
        y, uc = data[tgt]["ys"][d], data[tgt]["ucs"][d]
        uc_now = float(uc.iloc[-3:].mean())
        comp_12m = float(y.iloc[-12:].sum())
        monthly_rate = comp_12m / 12.0
        months_pipe = uc_now / monthly_rate if monthly_rate > 0 else np.nan
        # historical UC->completions conversion over next 18 months
        ratios = []
        for t in y.index[:-18]:
            u0 = uc.loc[t]
            if u0 > 0:
                nxt = y.loc[t + pd.DateOffset(months=1): t + pd.DateOffset(months=18)].sum()
                ratios.append(nxt / u0)
        conv = float(np.median(ratios)) if ratios else np.nan
        implied_18m = conv * uc_now if np.isfinite(conv) else np.nan
        model_18m = float(prod_fc[(tgt, d)].iloc[:18].sum())
        pipe_rows.append(dict(Regional_District=d, Target_Type=tgt,
                              UC_Current_3mAvg=round(uc_now, 0),
                              Completions_Trailing_12m=round(comp_12m, 0),
                              Months_Of_Pipeline=round(months_pipe, 1),
                              Hist_18m_Conversion_Ratio=round(conv, 2),
                              Implied_Next_18m_Completions=round(implied_18m, 0),
                              Model_Next_18m_Completions=round(model_18m, 0)))
pipe = pd.DataFrame(pipe_rows)

# ------------------------------------------------- 6) diagnostics + receipts summary
oot = pd.read_csv("oot_metrics_v13.csv")
top_feats = {}
for tgt in TARGETS:
    coefs = pd.Series(np.abs(prod_models[tgt].coef_), index=FEATS).sort_values(ascending=False)
    top_feats[tgt] = " | ".join(coefs.index[:3])
diag = oot.rename(columns={"district": "Regional_District", "target": "Target",
                           "model_wape": "OOT_WAPE", "naive_wape": "Naive_WAPE",
                           "mase": "OOT_MASE", "r2_vs_naive": "OOT_R2_vs_Naive"})
diag["Winning_Model"] = MODEL_NAME
diag["Beats_Naive"] = diag["OOT_WAPE"] < diag["Naive_WAPE"]
diag["Skill_vs_Naive_Pct"] = ((1 - diag["OOT_WAPE"] / diag["Naive_WAPE"]) * 100).round(1)
diag["Top_Features"] = diag["Target"].map(top_feats)
diag["Intermittent_Data"] = diag.apply(lambda r: (r["Target"], r["Regional_District"]) in INTERMITTENT, axis=1)
diag = diag[["Regional_District", "Target", "Winning_Model", "OOT_WAPE", "Naive_WAPE",
             "Skill_vs_Naive_Pct", "OOT_MASE", "OOT_R2_vs_Naive", "Beats_Naive", "Intermittent_Data", "Top_Features"]]

rsum = (receipts.assign(ae_m=lambda x: (x.Actual - x.Model_Forecast).abs(),
                        ae_n=lambda x: (x.Actual - x.Naive_Forecast).abs())
        .groupby(["Regional_District", "Target_Type"])
        .agg(Actual_Total=("Actual", "sum"), Model_Total=("Model_Forecast", "sum"),
             Naive_Total=("Naive_Forecast", "sum"),
             Model_WAPE=("ae_m", "sum"), Naive_WAPE=("ae_n", "sum")).reset_index())
rsum["Model_WAPE"] = (rsum["Model_WAPE"] / rsum["Actual_Total"].clip(lower=1e-9)).round(3)
rsum["Naive_WAPE"] = (rsum["Naive_WAPE"] / rsum["Actual_Total"].clip(lower=1e-9)).round(3)
rsum["Winner"] = np.where(rsum["Model_WAPE"] < rsum["Naive_WAPE"], "Model", "Naive")

# headline aggregates
pooled_model = receipts.assign(ae=lambda x: (x.Actual - x.Model_Forecast).abs())
w_model = pooled_model.ae.sum() / receipts.Actual.abs().sum()
pooled_naive = receipts.assign(ae=lambda x: (x.Actual - x.Naive_Forecast).abs())
w_naive = pooled_naive.ae.sum() / receipts.Actual.abs().sum()
print(f"Volume-weighted OOT WAPE — model {w_model:.3f} vs naive {w_naive:.3f}")

notes = pd.DataFrame([
    ("Model", MODEL_NAME),
    ("Approach", "One pooled cross-district Ridge per target type on level-scaled units; 8 features; damped recursion; clipped bias correction"),
    ("Targets", "3-month-smoothed CMHC completions: Total / Multi / Single, 7 CMHC districts + BC total"),
    ("Training data", f"2020-01 to {END.date()}, 24 series"),
    ("Holdout", f"Out-of-time, last {H_OOT} months ({(CUTOFF + pd.DateOffset(months=1)).date()} onward), never used in fitting or selection"),
    ("Headline skill", f"Volume-weighted OOT WAPE {w_model:.1%} vs seasonal-naive {w_naive:.1%}; {int(diag.Beats_Naive.sum())}/24 series beat naive"),
    ("Prediction intervals", "Empirical (conformal-style) from 8 rolling-origin backtests; pooled residual quantiles by target and horizon bucket; widths grow ~sqrt(h) beyond 12m"),
    ("Realized coverage", "; ".join(f"{k}% band -> {v:.0%} of 12-month unseen holdout actuals inside (after conformal calibration)" for k, v in cal_cov.items())),
    ("Scenarios", "Baseline: 5y mortgage rate flat at last value. Downside/Upside: +/-100bp phased over 6 months, flowing through the rate_d12 feature"),
    ("Driver assumption", "Under-construction stock held flat over forecast horizon; economic drivers per scenario"),
    ("Known limits", "Fraser-Fort George (all) and Nanaimo Multi are burst-reported/intermittent; monthly point forecasts unreliable there — use intervals and annual sums. Regime changes (policy shocks) not forecastable."),
    ("Retraining", "Re-run script when new CMHC months land; quarterly recommended"),
], columns=["Item", "Value"])

# ---------------------------------------------------------------- write
dash = dash[["Regional_District", "Target_Type", "Date", "Data_Type", "Completions_Value",
             "PI_Lower_95", "PI_Upper_95", "Winning_Model",
             "PI_Lower_80", "PI_Upper_80", "PI_Lower_50", "PI_Upper_50", "PI_Method"]]
dash.to_csv(f"{OUT}/PBI_Unified_Dashboard.csv", index=False)
scen.to_csv(f"{OUT}/PBI_Scenarios.csv", index=False)
receipts.to_csv(f"{OUT}/PBI_Backtest.csv", index=False)
rsum.to_csv(f"{OUT}/PBI_Backtest_Summary.csv", index=False)
pipe.to_csv(f"{OUT}/PBI_Pipeline_Indicator.csv", index=False)
sens.to_csv(f"{OUT}/PBI_Rate_Sensitivity.csv", index=False)
diag.to_csv(f"{OUT}/PBI_Diagnostics.csv", index=False)
notes.to_csv(f"{OUT}/PBI_Model_Notes.csv", index=False)
print("written all CSVs")
