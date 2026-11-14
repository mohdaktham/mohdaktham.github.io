# Mo Maghaireh: data analytics portfolio

Data analyst in Toronto. MSc in Management Analytics, Wilfrid Laurier University (2026), and BSc in Computer Science and Software Engineering.

**Live site: [mohdaktham.github.io](https://mohdaktham.github.io)**

## Projects

Each project has a case study on the site and its code in this repository.

| Project | Stack | What it shows |
| --- | --- | --- |
| [BC Housing completions forecast](projects/05-bc-housing-forecast/) | Python, Ridge, Power BI | 11.1% forecast error against 20.7% for a naive forecast on 12 held-out months, with a 36-month horizon (write-up only) |
| [Fraud model monitoring](projects/06-fraud-model-monitoring/) | Python, scikit-learn, pytest | Monthly AUC, KS, PSI and CSI checks that tell a broken data feed apart from a new fraud pattern (simulated data) |
| [Tessera, a SQL workbench](https://github.com/mohdaktham/tessera) | TypeScript, React, SQLite | A SQL workbench that runs in the browser and as a desktop app, with 102 automated tests ([live app](https://tesserasql.vercel.app)) |
| [Customer churn: drivers and revenue at risk](projects/03-customer-churn/) | Python, scikit-learn | Test AUC 0.837, and $445K of annualized revenue identified with high-risk customers |
| [Retail sales analytics in SQL](projects/02-sql-retail-analytics/) | SQL (CTEs, window functions), SQLite | Cohort retention, RFM segmentation and discount-loss diagnosis |
| [TTC subway delay analysis](projects/01-ttc-subway-delays/) | Python, pandas, Matplotlib | 64K+ real Toronto Open Data records, 126 days of lost service quantified |
| [Executive KPI dashboard in Excel](projects/04-excel-kpi-dashboard/) | Excel, openpyxl | 27 live formulas, zero errors, 4 native charts |

## More on GitHub

| Project | Stack | Repository |
| --- | --- | --- |
| Walmart retail sales forecasting (MGTA 611) | Python, XGBoost, LSTM, SHAP | [611-group-project](https://github.com/mohdaktham/projects/tree/main/611-group-project) |
| BC Housing: starts or registrations as the leading indicator (MGTA 621) | Python, regression, CMHC data | [621 Field Project](https://github.com/mohdaktham/projects/tree/main/621%20Field%20Project) |
| Vehicular network simulation with NS-3 and SUMO (INDUCE Lab) | Python, NS-3, SUMO | [NS-3_Sumo](https://github.com/mohdaktham/NS-3_Sumo) |
| BackTest Buddy, an equity strategy backtester | Python, Flask, Backtrader | [BackTest Buddy](https://github.com/mohdaktham/projects/tree/main/BackTest%20Buddy) |

## How the site is built

The site is plain HTML and CSS with no framework. A small Python script generates the pages, and the generated files are committed, so GitHub Pages serves them as they are.

| Path | What it is |
| --- | --- |
| `site/content.py` | All the text on the site: projects, skills, about |
| `site/build.py` | Turns that text into `index.html` and one case-study page per project |
| `site/check_links.py` | Checks that every internal link and image on the generated pages exists |
| `assets/` | Styles, fonts, images and the theme switch |
| `projects/` | One folder per project, with its code, data, charts and case-study page |

To change the site, edit `site/content.py`, then run:

```bash
python site/build.py
python site/check_links.py
```

Both scripts use only the Python standard library.

## Contact

mohammadaktham@gmail.com, [LinkedIn](https://linkedin.com/in/mo-maghaireh)
