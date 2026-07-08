# Customer Churn: Drivers, Prediction & Revenue at Risk

**Tools:** Python (pandas, scikit-learn, Matplotlib) · **Data:** IBM Telco Customer Churn — 7,032 customers

## Business question
26.6% of customers churn. Which ones, why, and how much revenue can a targeted retention campaign realistically protect?

## What I did
- Cleaned and explored the dataset, quantifying churn rates across contract type, tenure, internet service, and payment method
- Built a **logistic regression classifier (test AUC 0.837)** with balanced class weights, chosen deliberately for interpretability — every coefficient maps to an action a retention team can take
- Translated model scores into business terms: **$445K of annualized revenue sits with high-risk customers** (churn probability ≥ 0.7) in the test set alone
- Targeting the model's top-20% risk decile captures churners at **2.5× the base rate** — the efficiency case for scored outreach vs blanket discounts

## Key findings
- **Month-to-month contracts churn at 42.7%** vs 2.8% on two-year contracts — contract migration is the single biggest lever
- **The first 6 months are the danger zone**: 53% churn, falling to 9.5% after 4 years — onboarding investment pays off
- **Fiber-optic customers churn at 41.9%** vs 19% on DSL despite paying more — a price/value or service-quality red flag
- **Electronic-check payers churn at 45.3%**, ~3× auto-payment users — nudging customers to auto-pay is a cheap retention win

## Recommended retention playbook
1. Offer first-year discount for month-to-month → 1-year conversions on high-risk scores
2. Proactive 90-day onboarding check-ins for new fiber customers
3. Auto-pay signup incentive targeted at electronic-check payers

## Files
`churn_analysis.py` (full pipeline) · `charts/` (driver charts, coefficient plot) · `findings.txt` (auto-generated stats) · `data/`

## Run it
```bash
pip install pandas scikit-learn matplotlib
python churn_analysis.py
```
