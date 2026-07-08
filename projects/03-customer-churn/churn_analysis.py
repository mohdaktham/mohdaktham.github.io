"""
Telco Customer Churn -- Drivers & Prediction
Data: IBM Telco Customer Churn dataset (7,043 customers)
Author: Mo Maghaireh

EDA + logistic regression to identify churn drivers, then translates
model output into a revenue-at-risk estimate and retention playbook.
"""
import pandas as pd, numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, classification_report, confusion_matrix

plt.rcParams.update({"figure.dpi": 150, "font.size": 9, "axes.spines.top": False, "axes.spines.right": False})
BLUE, RED = "#1f6feb", "#d64545"

# ---------- load & clean ----------
df = pd.read_csv("data/telco_churn.csv")
df["TotalCharges"] = pd.to_numeric(df["TotalCharges"], errors="coerce")
df = df.dropna(subset=["TotalCharges"])
df["ChurnFlag"] = (df["Churn"] == "Yes").astype(int)
churn_rate = df["ChurnFlag"].mean()

# ---------- EDA ----------
by_contract = df.groupby("Contract")["ChurnFlag"].mean().sort_values(ascending=False)
by_tenure = df.groupby(pd.cut(df["tenure"], [0, 6, 12, 24, 48, 72], labels=["0-6m","7-12m","13-24m","25-48m","49-72m"]), observed=True)["ChurnFlag"].mean()
by_internet = df.groupby("InternetService")["ChurnFlag"].mean().sort_values(ascending=False)
by_payment = df.groupby("PaymentMethod")["ChurnFlag"].mean().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(10, 3.8))
by_contract.mul(100).plot.bar(ax=axes[0], color=RED, rot=15)
axes[0].set_title("Churn rate by contract type"); axes[0].set_ylabel("Churn %"); axes[0].set_xlabel("")
by_tenure.mul(100).plot.bar(ax=axes[1], color=BLUE, rot=0)
axes[1].set_title("Churn rate by tenure"); axes[1].set_xlabel("")
plt.tight_layout(); plt.savefig("charts/churn_drivers.png"); plt.close()

# ---------- model ----------
cat_cols = ["Contract","InternetService","PaymentMethod","OnlineSecurity","TechSupport","PaperlessBilling","SeniorCitizen","Partner","Dependents"]
X = pd.get_dummies(df[cat_cols].astype(str), drop_first=True)
X["tenure"] = df["tenure"]; X["MonthlyCharges"] = df["MonthlyCharges"]
y = df["ChurnFlag"]
Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=42)
sc = StandardScaler().fit(Xtr)
model = LogisticRegression(max_iter=2000, class_weight="balanced")
model.fit(sc.transform(Xtr), ytr)
proba = model.predict_proba(sc.transform(Xte))[:, 1]
auc = roc_auc_score(yte, proba)
pred = (proba >= 0.5).astype(int)
report = classification_report(yte, pred, target_names=["Stayed","Churned"])

coefs = pd.Series(model.coef_[0], index=X.columns).sort_values()
fig, ax = plt.subplots(figsize=(8, 5))
colors = [RED if v > 0 else BLUE for v in coefs.values]
coefs.plot.barh(ax=ax, color=colors)
ax.set_title(f"What drives churn? (logistic regression coefficients, AUC={auc:.2f})")
ax.set_xlabel("<- reduces churn | increases churn ->")
plt.tight_layout(); plt.savefig("charts/model_coefficients.png"); plt.close()

# ---------- business translation ----------
te = df.loc[Xte.index].copy(); te["churn_prob"] = proba
high_risk = te[te["churn_prob"] >= 0.7]
rev_at_risk = (high_risk["MonthlyCharges"].sum() * 12)
lift = te.sort_values("churn_prob", ascending=False).head(int(len(te)*0.2))["ChurnFlag"].mean() / te["ChurnFlag"].mean()

with open("findings.txt", "w") as f:
    f.write("TELCO CHURN ANALYSIS - KEY FINDINGS\n" + "="*40 + "\n\n")
    f.write(f"customers analyzed: {len(df)}\noverall churn rate: {churn_rate:.1%}\n")
    f.write(f"model test AUC: {auc:.3f}\n")
    f.write(f"top-20% risk decile lift: {lift:.1f}x\n")
    f.write(f"high-risk customers (p>=0.7) in test set: {len(high_risk)}\n")
    f.write(f"annualized revenue at risk (test set, p>=0.7): ${rev_at_risk:,.0f}\n\n")
    f.write("CHURN BY CONTRACT\n" + by_contract.round(3).to_string())
    f.write("\n\nCHURN BY TENURE\n" + by_tenure.round(3).to_string())
    f.write("\n\nCHURN BY INTERNET SERVICE\n" + by_internet.round(3).to_string())
    f.write("\n\nCHURN BY PAYMENT METHOD\n" + by_payment.round(3).to_string())
    f.write("\n\nCLASSIFICATION REPORT (test set)\n" + report)
print(open("findings.txt").read())
