"""
Everything the site says lives in this file. Edit the text here, then run
`python site/build.py` to regenerate the pages.

Text supports two bits of inline markup: **bold** and `code`.
"""

SITE = {
    "name": "Mo Maghaireh",
    "role": "Data analyst",
    "url": "https://mohdaktham.github.io",
    "email": "mohammadaktham@gmail.com",
    "linkedin": "https://linkedin.com/in/mo-maghaireh",
    "github": "https://github.com/mohdaktham",
    "repo": "https://github.com/mohdaktham/mohdaktham.github.io",
    "description": (
        "Mo Maghaireh is a data analyst in Toronto who builds models and the checks that tell "
        "you whether to trust them, in SQL, Python and Power BI."
    ),
    "headline": "I build models, and the checks that tell you whether to trust them.",
    "intro": (
        "I'm a data analyst in Toronto working in SQL, Python and Power BI. I hold an MSc in "
        "Management Analytics from Wilfrid Laurier University (2026), and most recently "
        "forecast housing supply for BC Housing. I'm looking for data analyst and data "
        "science roles."
    ),
}

REPO_TREE = SITE["repo"] + "/tree/main/projects/"

# ---------------------------------------------------------------------------
# Projects. The order here is the order on the home page.
#
# "evidence" is what sits beside each project on the home page: the check that
# backs up its claim. It is one of:
#   {"kind": "bars",  "bars": [...], "caption": "..."}
#   {"kind": "stats", "stats": [(number, label), ...], "caption": "..."}
#   {"kind": "image", "src": "...", "alt": "...", "size": (w, h), "caption": "..."}
# ---------------------------------------------------------------------------

PROJECTS = [
    {
        "slug": "05-bc-housing-forecast",
        "short": "BC Housing",
        "kicker": "Client engagement",
        "title": "BC Housing completions forecast",
        "finding": (
            "36-month forecasts of housing completions for every BC regional district, "
            "with error cut nearly in half against a naive forecast."
        ),
        "tools": ["Python", "scikit-learn", "Time series", "Power BI", "DAX"],
        "evidence": {
            "kind": "stats",
            "stats": [
                ("83%", "of held-out actuals fell inside the 80% prediction band"),
                ("24", "regional series forecast from one pooled model"),
            ],
            "caption": "Backtested on 12 months the model never saw.",
        },
        "summary": (
            "Monthly housing completions, forecast 36 months ahead for every regional district "
            "in British Columbia, with calibrated uncertainty bands and mortgage-rate "
            "scenarios, delivered as an interactive Power BI dashboard."
        ),
        "context": (
            "Consulting engagement with BC Housing through Wilfrid Laurier University, January "
            "to August 2026. My part was the data preparation, the forecasting models and the "
            "Power BI build. The results and the dashboard were presented to agency staff and "
            "programme leads."
        ),
        "stats": [
            ("11.1%", "forecast error (WAPE), against 20.7% for a naive forecast"),
            ("36 months", "forecast horizon"),
            ("83%", "of actuals inside the 80% band"),
            ("8", "data feeds into Power BI"),
        ],
        "check": {
            "bars": [
                {"label": "This model", "value": 11.1, "display": "11.1%", "tone": "signal"},
                {"label": "Naive forecast", "value": 20.7, "display": "20.7%", "tone": "baseline"},
            ],
            "caption": (
                "Forecast error (WAPE) on the BC total series over 12 months the model never "
                "saw. Lower is better."
            ),
        },
        "sections": [
            {
                "h": "The question",
                "p": [
                    "How many homes will be completed in each BC regional district over the "
                    "next 36 months, how wide is the uncertainty around that number, and how "
                    "does it move if mortgage rates change?"
                ],
            },
            {
                "h": "What I did",
                "ul": [
                    "Merged more than 36 years of CMHC housing data with economic indicators: "
                    "mortgage rates, the policy rate and building permits.",
                    "Fitted one **pooled Ridge regression** across all districts, using lags of "
                    "the target, lags of the under-construction pipeline, seasonal encodings and "
                    "12-month mortgage-rate changes with a 6-month lag.",
                    "Scaled each district using only past data (shifted trailing means), so "
                    "districts of very different sizes share one model with **no look-ahead "
                    "leakage**.",
                    "Built empirical 50, 80 and 95% prediction intervals from the backtest errors.",
                    "Added a scenario engine: the baseline against mortgage-rate paths 100 basis "
                    "points higher and lower, with a table of forecast change per 100 basis points.",
                    "Cross-checked the forecasts against units physically under construction, "
                    "using 18-month conversion ratios.",
                    "Wrote the outputs as eight data feeds for the Power BI dashboard, covering "
                    "forecasts, scenarios, backtests, diagnostics and rate sensitivity.",
                ],
            },
            {
                "h": "What I found",
                "ul": [
                    "**11.1% error against 20.7% for the naive benchmark** on the BC total "
                    "series, over 12 months held out of training.",
                    "**The model beats naive on the large majority of the 24 regional series**, "
                    "not only on the provincial total.",
                    "**The uncertainty bands hold up:** 83% of held-out actuals landed inside "
                    "the 80% band.",
                ],
            },
            {
                "h": "What is published",
                "p": [
                    "This is a write-up only. The forecasting script, its outputs and the model "
                    "card belong to the client engagement and are not published, and the CMHC "
                    "source workbook is not shared for data-sharing reasons."
                ],
            },
        ],
        "links": [("Read the write-up on GitHub", REPO_TREE + "05-bc-housing-forecast")],
    },
    {
        "slug": "06-fraud-model-monitoring",
        "short": "Fraud monitoring",
        "kicker": "Model monitoring, simulated data",
        "title": "Fraud model monitoring",
        "finding": (
            "A monthly report that told a broken data feed apart from a new fraud pattern, "
            "on a year of simulated card transactions with three planted events."
        ),
        "tools": ["Python", "scikit-learn", "pandas", "pytest", "Matplotlib"],
        "evidence": {
            "kind": "bars",
            "max": 1.0,
            "bars": [
                {"label": "Baseline AUC", "value": 0.957, "display": "0.957", "tone": "signal"},
                {"label": "New fraud pattern", "value": 0.710, "display": "0.710", "tone": "fault"},
            ],
            "caption": (
                "No input and no score shifted that month. Only outcome monitoring caught the drop."
            ),
        },
        "summary": (
            "A fraud model that worked at launch can quietly stop working. This project builds "
            "the monthly checks that catch it, and shows them telling a data problem apart from "
            "a model problem."
        ),
        "context": (
            "Simulated data, built to practise the monthly monitoring a bank runs on its fraud "
            "models: 100,000 card transactions a month for 12 months, with three planted events. "
            "No real customer data is used."
        ),
        "stats": [
            ("0.957", "baseline AUC, validated out of time"),
            ("0.78", "input shift (CSI) on the faulty feed"),
            ("0.710", "AUC after the new fraud pattern"),
            ("6", "unit tests on the metric functions"),
        ],
        "check": {
            "max": 1.0,
            "bars": [
                {"label": "Baseline AUC", "value": 0.957, "display": "0.957", "tone": "signal"},
                {"label": "June, online spending shift", "value": 0.943, "display": "0.943", "tone": "baseline"},
                {"label": "August, feed fault", "value": 0.909, "display": "0.909", "tone": "baseline"},
                {"label": "October, new fraud pattern", "value": 0.710, "display": "0.710", "tone": "fault"},
            ],
            "caption": (
                "Ranking power (AUC) at each planted event. All three were flagged, but only the "
                "new fraud pattern broke the ranking. The feed fault showed up in the inputs instead."
            ),
        },
        "sections": [
            {
                "h": "The question",
                "p": [
                    "Which numbers should be checked every month, and how do you tell a data "
                    "problem from a model problem before deciding what to do about it?"
                ],
            },
            {
                "h": "What I did",
                "ul": [
                    "Trained a gradient-boosted fraud model on two months of transactions and "
                    "validated it out of time on the third month, which became the baseline.",
                    "Set the alert cut-off for a 1% alert rate, then scored nine production "
                    "months and compared each one with the baseline.",
                    "Wrote the checks as reusable functions that work on any score, including a "
                    "vendor score whose internals you can't see: AUC and Gini, KS, PSI on the "
                    "score, CSI on every input, alert rate, share of fraud cases and fraud "
                    "dollars caught, and false alarms per fraud caught.",
                    "Built in label delay: the report runs as of January 2026, so November and "
                    "December performance is provisional, because fraud is confirmed weeks "
                    "after the transaction.",
                    "Added amber and red thresholds that give every month a status and a "
                    "plain-language reason, plus unit tests for the metric functions.",
                ],
            },
            {
                "h": "What the monitoring caught",
                "monitor": {
                    "csv": "outputs/monitoring_report.csv",
                    "title": "The year, month by month",
                    "hint": "Choose a month to see what the report said.",
                    "start": "2025-10",
                    "notes": {
                        "2025-03": "The baseline. The model was validated on this month, out of time.",
                        "2025-04": "Every check within thresholds.",
                        "2025-05": "Every check within thresholds.",
                        "2025-06": (
                            "Planted event: online spending rose. One input, card_present, drifted "
                            "past the watch line, but the model still ranked well."
                        ),
                        "2025-07": "Every check within thresholds.",
                        "2025-08": (
                            "Planted event: a feed delivered distance_from_home as 0 for 40% of "
                            "transactions. The input check caught it, and fraud cases caught fell."
                        ),
                        "2025-09": "Back within thresholds once the feed fault ended.",
                        "2025-10": (
                            "Planted event: a new fraud type that looks like everyday spending. "
                            "No input or score moved, yet ranking power dropped."
                        ),
                        "2025-11": (
                            "Inputs and scores are stable. Performance is provisional until the "
                            "fraud labels mature."
                        ),
                        "2025-12": (
                            "Inputs and scores are stable. Performance is provisional until the "
                            "fraud labels mature."
                        ),
                    },
                    "caption": (
                        "From the project's monitoring report (simulated data). August and October "
                        "are both red, for opposite reasons: in August an input moved, in October "
                        "nothing did."
                    ),
                },
                "table": {
                    "head": ["Month", "What happened", "What the report showed", "Status", "Right response"],
                    "rows": [
                        [
                            "June",
                            "Online spending rose: card-not-present share from 30% to 50%",
                            "CSI on `card_present` 0.17; AUC 0.943; alert rate up to 1.4%",
                            "Amber",
                            "Watch it. The inputs drifted but the model still ranks well; plan for more alerts",
                        ],
                        [
                            "August",
                            "A feed delivered `distance_from_home` as 0 for 40% of transactions",
                            "CSI on distance 0.78; alert rate down to 0.6%; fraud cases caught down from 44.7% to 25.9%",
                            "Red",
                            "A data problem, not a model problem: fix the feed and rescore. No retraining",
                        ],
                        [
                            "October",
                            "A new fraud type that looks like everyday spending, 36% of fraud",
                            "No input or score shift (PSI 0.000); AUC down to 0.710; fraud cases caught 34.2%",
                            "Red",
                            "A model problem: retrain on the newly labelled cases, add an interim rule, brief the fraud team",
                        ],
                        [
                            "November, December",
                            "The new pattern continues",
                            "Stability checks clean; performance waits for labels",
                            "Pending",
                            "Stability checks alone would have said all was well",
                        ],
                    ],
                },
                "figs": [
                    {
                        "src": "charts/performance.png",
                        "alt": "AUC, KS and share of fraud caught by month, with the three events marked",
                        "caption": "Ranking power held until the new fraud pattern appeared.",
                    }
                ],
            },
            {
                "h": "What I found",
                "ul": [
                    "**Check the data before blaming the model.** The August feed fault cut fraud "
                    "caught from 44.7% to 25.9%, yet the score PSI (0.073) stayed under the watch "
                    "line. Only the input-level check, a CSI of 0.78 on distance, pointed to the cause.",
                    "**Drift is not the same as degradation.** June's jump in online spending "
                    "pushed an input past the watch line, but ranking power barely moved "
                    "(AUC 0.943 against 0.957).",
                    "**The most dangerous change moves nothing you can see.** The October fraud "
                    "pattern left every input and the score distribution unchanged. Only outcome "
                    "monitoring found it, and only once labels matured, which is why stability "
                    "checks and performance checks are both needed.",
                    "**Track dollars as well as cases.** The new fraud was small-ticket, so fraud "
                    "dollars caught held up in October (60.6%) while fraud cases caught fell. "
                    "Either measure alone tells half the story.",
                ],
                "figs": [
                    {
                        "src": "charts/stability.png",
                        "alt": "Score PSI and input CSI by month",
                        "caption": "Score and input stability by month.",
                    },
                    {
                        "src": "charts/alerts.png",
                        "alt": "Alert rate and false alarms per fraud caught by month",
                        "caption": "Alert volume and false alarms per fraud caught.",
                    },
                ],
            },
            {
                "h": "Files",
                "table": {
                    "head": ["File", "What it is"],
                    "rows": [
                        ["`simulate.py`", "Transaction generator with the three planted events"],
                        ["`monitoring/metrics.py`", "PSI, KS, AUC and Gini, and alert metrics as reusable functions"],
                        ["`run_monitoring.py`", "Trains the model, scores each month, writes the report, charts and findings"],
                        ["`tests/test_metrics.py`", "Unit tests for the metric functions"],
                        ["`outputs/monitoring_report.csv`", "One row per month: performance, stability, status and reason"],
                    ],
                },
            },
            {
                "h": "Run it",
                "code": "pip install -r requirements.txt\npython run_monitoring.py\npytest tests",
            },
        ],
        "links": [("View the code on GitHub", REPO_TREE + "06-fraud-model-monitoring")],
    },
    {
        "slug": "tessera",
        "short": "Tessera",
        "kicker": "Software, live app",
        "title": "Tessera, a SQL workbench",
        "finding": (
            "A SQL workbench that runs in the browser and as a desktop app: import a file, "
            "query it, chart the result and pin it to a dashboard."
        ),
        "tools": ["TypeScript", "React", "SQLite (WebAssembly)", "Electron", "Playwright"],
        "evidence": {
            "kind": "image",
            "src": "assets/img/tessera-dashboard.webp",
            "alt": "Tessera's dashboard showing revenue, orders and growth charts",
            "size": (1600, 1000),
            "caption": "102 automated tests run on Windows, macOS and Linux on every change.",
        },
        "summary": (
            "Tessera turns CSV, JSON and SQLite files into tables you can query with SQL, chart "
            "and pin to a dashboard. It runs as a website and as a desktop app, and the data "
            "never leaves your machine."
        ),
        "context": (
            "Open the live app and choose Load sample data to try it with 60,000 orders and a "
            "ready-made dashboard."
        ),
        "stats": [
            ("102", "automated tests: 82 unit, 20 end to end"),
            ("3", "operating systems tested on every change"),
            ("2", "ways to run it, website and desktop, from one codebase"),
            ("0", "uploads: your data stays on your machine"),
        ],
        "hero_image": {
            "src": "assets/img/tessera-query.webp",
            "alt": "Tessera's query editor with a SQL query and its results",
            "size": (1600, 1000),
        },
        "sections": [
            {
                "h": "What it does",
                "ul": [
                    "**Brings data in:** import CSV, TSV, JSON or a SQLite database by file picker "
                    "or drag and drop, with column types inferred from the data.",
                    "**Queries it:** a SQL editor with autocomplete that knows your tables, "
                    "multiple tabs, and SQLite 3 with CTEs and window functions.",
                    "**Explains itself:** a query-plan view that flags full table scans, and a "
                    "column profile with completeness, range, median and a histogram.",
                    "**Shows the answer:** bar, line, area, scatter and pie charts, pinned to a "
                    "dashboard that re-runs its queries when the data changes.",
                ],
                "figs": [
                    {
                        "src": "assets/img/tessera-dashboard.webp",
                        "alt": "Tessera's dashboard showing revenue, orders and growth charts",
                        "size": (1600, 1000),
                        "caption": "The dashboard: each tile is a saved query.",
                        "root": True,
                    }
                ],
            },
            {
                "h": "How it is built",
                "ul": [
                    "**SQL runs off the main thread.** SQLite is compiled to WebAssembly and runs "
                    "in a Web Worker, so a heavy query never freezes the interface.",
                    "**One codebase, two hosts.** A thin platform layer hides whether the app is "
                    "inside Electron or a browser, which is how the same code ships as a website.",
                    "**The page is treated as untrusted.** The desktop shell is sandboxed, every "
                    "message between processes is validated, and a strict content security "
                    "policy blocks remote and inline scripts.",
                    "**It works on a phone.** Below tablet width the sidebar becomes a drawer and "
                    "the toolbars collapse to icons.",
                ],
                "figs": [
                    {
                        "src": "assets/img/tessera-phone.webp",
                        "alt": "Tessera on a phone: the query editor, the sidebar drawer and the dashboard",
                        "size": (1600, 1069),
                        "caption": "The same app at phone width.",
                        "root": True,
                    }
                ],
            },
            {
                "h": "How it is tested",
                "ul": [
                    "**82 unit and component tests** cover the query engine against a real SQLite "
                    "build, file parsing, type inference, sorting and charts.",
                    "**9 desktop tests** launch the real app and check the full path: load data, "
                    "run SQL, handle an error, pin a chart, and survive a restart.",
                    "**11 browser tests** run the website at desktop and phone sizes behind its "
                    "production security headers, and fail on any policy violation.",
                    "All of it runs on Windows, macOS and Linux on every change.",
                ],
            },
        ],
        "links": [
            ("Open the live app", "https://tesserasql.vercel.app"),
            ("View the code on GitHub", "https://github.com/mohdaktham/tessera"),
            ("Download the desktop app", "https://github.com/mohdaktham/tessera/releases"),
        ],
    },
    {
        "slug": "03-customer-churn",
        "short": "Churn",
        "kicker": "Classification",
        "title": "Customer churn: drivers and revenue at risk",
        "finding": (
            "An interpretable churn model for 7,032 telecom customers, turned into a three-step "
            "retention playbook and a figure for the revenue at stake."
        ),
        "tools": ["Python", "scikit-learn", "pandas", "Matplotlib"],
        "evidence": {
            "kind": "bars",
            "bars": [
                {"label": "Model's top 20%", "value": 2.5, "display": "2.5x", "tone": "signal"},
                {"label": "No targeting", "value": 1.0, "display": "1.0x", "tone": "baseline"},
            ],
            "caption": "Churners reached per customer contacted, on a held-out test set (AUC 0.837).",
        },
        "summary": (
            "26.6% of customers churn. This project finds which ones and why, and puts a number "
            "on how much revenue a targeted retention campaign could protect."
        ),
        "context": "Data: IBM Telco Customer Churn, 7,032 customers.",
        "stats": [
            ("0.837", "AUC on the held-out test set"),
            ("$445K", "annualized revenue with high-risk customers"),
            ("2.5x", "churners reached by targeting the top 20%"),
            ("42.7%", "churn on month-to-month contracts"),
        ],
        "check": {
            "bars": [
                {"label": "Model's top 20%", "value": 2.5, "display": "2.5x", "tone": "signal"},
                {"label": "No targeting", "value": 1.0, "display": "1.0x", "tone": "baseline"},
            ],
            "caption": (
                "Churners reached per customer contacted, compared with the base rate, measured "
                "on customers the model was not trained on."
            ),
        },
        "sections": [
            {
                "h": "The question",
                "p": [
                    "Which customers churn, why, and how much revenue can a targeted retention "
                    "campaign realistically protect?"
                ],
            },
            {
                "h": "What I did",
                "ul": [
                    "Cleaned and explored the dataset, measuring churn rates across contract "
                    "type, tenure, internet service and payment method.",
                    "Built a **logistic regression classifier** with balanced class weights, "
                    "chosen for interpretability: every coefficient maps to an action a "
                    "retention team can take.",
                    "Translated model scores into business terms: **$445K of annualized revenue** "
                    "sits with high-risk customers (churn probability of 0.7 or more) in the "
                    "test set alone.",
                    "Showed the efficiency case for scored outreach over blanket discounts: the "
                    "model's top 20% by risk reaches churners at 2.5 times the base rate.",
                ],
            },
            {
                "h": "What I found",
                "ul": [
                    "**Month-to-month contracts churn at 42.7%** against 2.8% on two-year "
                    "contracts, so contract migration is the single biggest lever.",
                    "**The first 6 months are the danger zone:** 53% churn, falling to 9.5% after "
                    "4 years, so onboarding investment pays off.",
                    "**Fiber-optic customers churn at 41.9%** against 19% on DSL despite paying "
                    "more, a price or service-quality red flag.",
                    "**Electronic-check payers churn at 45.3%**, about 3 times auto-payment users, "
                    "so nudging customers to auto-pay is a cheap retention win.",
                ],
                "figs": [
                    {
                        "src": "charts/churn_drivers.png",
                        "alt": "Churn rate by contract type and by tenure",
                        "caption": "Churn rate by contract type and by tenure.",
                    },
                    {
                        "src": "charts/model_coefficients.png",
                        "alt": "Logistic regression coefficients, the drivers of churn",
                        "caption": "Model coefficients: what pushes churn risk up and down.",
                    },
                ],
            },
            {
                "h": "Recommended playbook",
                "ol": [
                    "Offer a first-year discount for month-to-month customers with high risk "
                    "scores who move to a one-year contract.",
                    "Run proactive 90-day onboarding check-ins for new fiber customers.",
                    "Target an auto-pay sign-up incentive at electronic-check payers.",
                ],
            },
            {
                "h": "Run it",
                "code": "pip install pandas scikit-learn matplotlib\npython churn_analysis.py",
            },
        ],
        "links": [("View the code on GitHub", REPO_TREE + "03-customer-churn")],
    },
    {
        "slug": "02-sql-retail-analytics",
        "short": "SQL retail",
        "kicker": "SQL",
        "title": "Retail sales analytics in SQL",
        "finding": (
            "A flat retail file normalized into a four-table schema, then seven queries that "
            "find where profit is made, where discounts destroy it and who to win back."
        ),
        "tools": ["SQL", "SQLite", "CTEs", "Window functions", "Python"],
        "evidence": {
            "kind": "stats",
            "stats": [
                ("7", "analytical queries over a 4-table schema"),
                ("82", "high-value customers found at risk of leaving"),
            ],
            "caption": "Every result rebuilds from the raw file with two scripts.",
        },
        "summary": (
            "A national retailer wants to know where profit is actually made, which discounting "
            "destroys margin, and which customers are worth retention spend. Seven SQL queries "
            "answer it."
        ),
        "context": "Data: Superstore retail dataset, 9,994 order lines from 2015 to 2018.",
        "stats": [
            ("7", "analytical queries"),
            ("4", "tables in the normalized schema"),
            ("$2.3M", "revenue analyzed"),
            ("82", "at-risk customers identified"),
        ],
        "sections": [
            {
                "h": "The question",
                "p": [
                    "Where is profit actually made, which discounting behaviour destroys margin, "
                    "and which customers are worth retention spend?"
                ],
            },
            {
                "h": "What I did",
                "ul": [
                    "**Normalized a flat 21-column CSV into a 4-table relational schema** "
                    "(`customers`, `products`, `orders`, `order_items`) with indexes.",
                    "Wrote **7 analytical queries** covering year-over-year growth, profitability "
                    "ranking, discount-loss diagnosis, 12-month cohort retention, RFM customer "
                    "segmentation and shipping lag.",
                    "Scripted the whole run: one script builds the database from the raw file, "
                    "another executes every query and exports each result as a CSV.",
                ],
            },
            {
                "h": "What I found",
                "ul": [
                    "Revenue grew from **$484K in 2015 to $733K in 2018**, up 29.5% and 20.4% in "
                    "the last two years, while profit margin improved from 10.2% to 12.7%.",
                    "**Tables lose $17.7K despite heavy discounting** (26% on average). Bookcases "
                    "and Supplies also run negative. Recommendation: cap Table discounts at 15%.",
                    "**Copiers are the hidden star:** only 8th in revenue but first in profit, "
                    "$55.6K at a 37% margin.",
                    "RFM segmentation found **82 at-risk customers averaging $4,444 in lifetime "
                    "sales** who haven't ordered in about 200 days, the best win-back target.",
                    "The 12-month repeat-purchase rate for the 2015 cohort is **69%**, and rises "
                    "for later cohorts.",
                ],
            },
            {
                "h": "SQL techniques used",
                "p": [
                    "Joins across a normalized schema, CTEs, the window functions `LAG`, `RANK`, "
                    "`ROW_NUMBER` and `NTILE`, conditional aggregation, date arithmetic with "
                    "`julianday`, and `HAVING` filters."
                ],
            },
            {
                "h": "Run it",
                "code": (
                    "pip install pandas\n"
                    "python build_db.py      # builds superstore.db from superstore.csv\n"
                    "python run_queries.py   # runs all 7 queries, exports to outputs/"
                ),
            },
        ],
        "links": [("View the queries on GitHub", REPO_TREE + "02-sql-retail-analytics")],
    },
    {
        "slug": "01-ttc-subway-delays",
        "short": "TTC delays",
        "kicker": "Toronto Open Data",
        "title": "TTC subway delay analysis",
        "finding": (
            "Two years of real subway delay logs, cleaned and quantified: 126 days of service "
            "lost, and the leading causes are people, not equipment."
        ),
        "tools": ["Python", "pandas", "NumPy", "Matplotlib"],
        "evidence": {
            "kind": "stats",
            "stats": [
                ("64,485", "raw records from Toronto Open Data"),
                ("126 days", "of service time lost to delays"),
            ],
            "caption": "One script regenerates every chart and figure from the raw extracts.",
        },
        "summary": (
            "The TTC logs every subway delay. This project works out where service time is "
            "actually lost, and what would give riders the biggest reliability improvement "
            "per dollar."
        ),
        "context": (
            "Data: 64,485 delay records for 2024 and 2025 from the City of Toronto Open Data portal."
        ),
        "stats": [
            ("64,485", "raw records"),
            ("22,814", "delay incidents after cleaning"),
            ("126 days", "of service time lost"),
            ("8.0 min", "average delay, median 5"),
        ],
        "sections": [
            {
                "h": "The question",
                "p": [
                    "Where is subway service time actually being lost, and what would give "
                    "riders the biggest reliability improvement per dollar?"
                ],
            },
            {
                "h": "What I did",
                "ul": [
                    "Combined and cleaned two years of raw delay logs from Excel and CSV "
                    "extracts, standardized station names, and joined the TTC's delay-code "
                    "lookup table to translate codes into readable causes.",
                    "Filtered to **22,814 true delay incidents** across Lines 1, 2 and 4, and "
                    "measured lost service time by line, station, hour, weekday and cause.",
                    "Wrote one analysis script that regenerates every chart and a findings "
                    "summary from the raw files.",
                ],
            },
            {
                "h": "What I found",
                "ul": [
                    "**126 days of service time lost:** 181,700 delay minutes over the period, "
                    "averaging 8.0 minutes per incident.",
                    "**Line 1 loses the most time** (100,290 minutes across 13,078 incidents), "
                    "but Line 2 delays run longer on average, 8.3 against 7.7 minutes.",
                    "**Delays peak at 8 AM and between 4 and 5 PM**, exactly when capacity "
                    "matters most.",
                    "**The top causes are people, not equipment:** disorderly patrons, medical "
                    "emergencies and unauthorized track-level access dominate, which supports "
                    "investment in platform safety and station staffing over purely mechanical fixes.",
                    "Eglinton, Kipling, St George and Kennedy are the highest-loss stations, all "
                    "major interchange or terminal points.",
                ],
                "figs": [
                    {
                        "src": "charts/delay_by_hour.png",
                        "alt": "Delay incidents by hour of day, peaking at 8 AM and late afternoon",
                        "caption": "Delays cluster around the morning and afternoon peaks.",
                    },
                    {
                        "src": "charts/top_stations.png",
                        "alt": "The ten stations with the most delay minutes",
                        "caption": "Stations with the most service time lost.",
                    },
                ],
            },
            {
                "h": "Run it",
                "code": "pip install pandas numpy matplotlib openpyxl\npython ttc_delay_analysis.py",
            },
        ],
        "links": [("View the code on GitHub", REPO_TREE + "01-ttc-subway-delays")],
    },
    {
        "slug": "04-excel-kpi-dashboard",
        "short": "Excel KPIs",
        "kicker": "Excel",
        "title": "Executive KPI dashboard in Excel",
        "finding": (
            "A three-sheet executive workbook where every number is a live formula, built by a "
            "script so it can be regenerated from the data."
        ),
        "tools": ["Excel", "openpyxl", "Python"],
        "evidence": {
            "kind": "stats",
            "stats": [
                ("27", "live formulas feeding 6 KPI cards and 4 charts"),
                ("0", "formula errors after automated recalculation"),
            ],
            "caption": "Change the data sheet and the whole dashboard recalculates.",
        },
        "summary": (
            "An executive dashboard workbook for the Superstore retail dataset: six KPI cards "
            "and four native Excel charts, with no hardcoded numbers."
        ),
        "context": "Data: Superstore retail dataset, 2015 to 2018.",
        "stats": [
            ("27", "live formulas"),
            ("0", "formula errors"),
            ("4", "native Excel charts"),
            ("$2.30M", "revenue summarized"),
        ],
        "sections": [
            {
                "h": "What it is",
                "ul": [
                    "**Dashboard sheet:** 6 KPI cards (revenue, profit, margin, orders, average "
                    "order value, best month) and 4 native Excel charts: monthly revenue trend, "
                    "sales and profit by category, revenue by segment, and sales by region.",
                    "**Data sheet:** clean monthly, category, segment and region aggregates that "
                    "feed every KPI.",
                    "**Top Products sheet:** a sortable, filterable sub-category table with live "
                    "margin formulas.",
                ],
            },
            {
                "h": "Why it holds up",
                "ul": [
                    "**Every KPI is a live Excel formula** referencing the Data sheet. Change the "
                    "data and the whole dashboard recalculates.",
                    "Delivered with **zero formula errors**, confirmed by an automated "
                    "recalculation of the workbook.",
                    "Follows finance formatting conventions: whole-dollar currency, one-decimal "
                    "percentages and negatives in parentheses.",
                ],
            },
            {
                "h": "Headline numbers",
                "p": [
                    "Total revenue of $2.30M and profit of $286K, a 12.5% margin, across 5,009 "
                    "orders. Technology is the top category and the West region leads sales."
                ],
            },
        ],
        "links": [("View the workbook on GitHub", REPO_TREE + "04-excel-kpi-dashboard")],
    },
]

# ---------------------------------------------------------------------------
# The evidence shown beside the headline on the home page.
# ---------------------------------------------------------------------------

HERO_SLIDES = [
    {
        "tab": "Forecasting",
        "slug": "05-bc-housing-forecast",
        "title": "Forecasting housing completions for BC Housing",
        "bars": [
            {"label": "This model", "value": 11.1, "display": "11.1%", "tone": "signal"},
            {"label": "Naive forecast", "value": 20.7, "display": "20.7%", "tone": "baseline"},
        ],
        "caption": "Forecast error on 12 months the model never saw. Lower is better.",
    },
    {
        "tab": "Monitoring",
        "slug": "06-fraud-model-monitoring",
        "title": "Monitoring a fraud model on simulated data",
        "max": 1.0,
        "bars": [
            {"label": "Baseline AUC", "value": 0.957, "display": "0.957", "tone": "signal"},
            {"label": "New fraud pattern", "value": 0.710, "display": "0.710", "tone": "fault"},
        ],
        "caption": "No input and no score shifted that month. Only outcome monitoring caught the drop.",
    },
    {
        "tab": "Targeting",
        "slug": "03-customer-churn",
        "title": "Finding the customers most likely to churn",
        "bars": [
            {"label": "Model's top 20%", "value": 2.5, "display": "2.5x", "tone": "signal"},
            {"label": "No targeting", "value": 1.0, "display": "1.0x", "tone": "baseline"},
        ],
        "caption": "Churners reached per customer contacted, on a held-out test set (AUC 0.837).",
    },
]

# ---------------------------------------------------------------------------
# Skills, mapped to the projects that show them. Keys are project slugs.
# ---------------------------------------------------------------------------

SKILLS = [
    ("SQL", ["tessera", "02-sql-retail-analytics", "05-bc-housing-forecast"]),
    (
        "Python and pandas",
        [
            "05-bc-housing-forecast",
            "06-fraud-model-monitoring",
            "03-customer-churn",
            "02-sql-retail-analytics",
            "01-ttc-subway-delays",
            "04-excel-kpi-dashboard",
        ],
    ),
    ("Forecasting and regression", ["05-bc-housing-forecast"]),
    ("Classification", ["06-fraud-model-monitoring", "03-customer-churn"]),
    (
        "Validation and monitoring",
        ["05-bc-housing-forecast", "06-fraud-model-monitoring", "03-customer-churn"],
    ),
    ("Data cleaning and modelling", ["05-bc-housing-forecast", "02-sql-retail-analytics", "01-ttc-subway-delays"]),
    ("Dashboards and BI", ["05-bc-housing-forecast", "04-excel-kpi-dashboard", "tessera"]),
    ("Excel", ["04-excel-kpi-dashboard"]),
    ("Automated testing", ["tessera", "06-fraud-model-monitoring"]),
    ("Software engineering", ["tessera"]),
]

TOOLKIT = [
    ("Querying and data", "SQL (joins, CTEs, window functions), SQLite and MySQL, data modelling, Python (pandas, NumPy), R"),
    ("Models and statistics", "Logistic and Ridge regression, gradient boosting, time-series forecasting, out-of-time validation, prediction intervals, missing-data imputation"),
    ("Monitoring and quality", "AUC, Gini and KS, PSI and CSI drift checks, alert and false-alarm rates, validation checks, unit testing with pytest"),
    ("BI and communication", "Power BI (DAX, data modelling), Tableau, Excel dashboards, Matplotlib, presenting models to non-technical audiences, Git"),
]

# ---------------------------------------------------------------------------
# Coursework and research that lives in other repositories.
# ---------------------------------------------------------------------------

MORE = [
    {
        "title": "Walmart retail sales forecasting",
        "kicker": "Deep learning, MGTA 611",
        "text": (
            "Weekly sales prediction across 45 stores: feature engineering for holidays, rolling "
            "statistics and markdowns, an XGBoost baseline with a holiday-weighted loss, a tuned "
            "LSTM, and SHAP to explain store-level demand drivers."
        ),
        "url": "https://github.com/mohdaktham/projects/tree/main/611-group-project",
    },
    {
        "title": "BC Housing: starts or registrations as the leading indicator",
        "kicker": "Client analysis, MGTA 621",
        "text": (
            "Field project on which measure better predicts completions. Quantified conversion "
            "rates and time lags from registration to start to completion across 36 years of "
            "CMHC data."
        ),
        "url": "https://github.com/mohdaktham/projects/tree/main/621%20Field%20Project",
    },
    {
        "title": "Vehicular network simulation with NS-3 and SUMO",
        "kicker": "Research, INDUCE Lab, UAE University",
        "text": (
            "Simulation framework for vehicular ad hoc network research, linking SUMO traffic "
            "simulation with NS-3 network simulation, with validation checks in the data "
            "collection pipeline."
        ),
        "url": "https://github.com/mohdaktham/NS-3_Sumo",
    },
    {
        "title": "BackTest Buddy, an equity strategy backtester",
        "kicker": "Web app, finance",
        "text": (
            "Web application for testing trading strategies against historical prices: define "
            "entry and exit rules and get back the Sharpe ratio and maximum drawdown."
        ),
        "url": "https://github.com/mohdaktham/projects/tree/main/BackTest%20Buddy",
    },
]

ABOUT = [
    "I'm a data analyst based in Toronto. I hold an MSc in Management Analytics from Wilfrid "
    "Laurier University (2026) and a BSc in Computer Science and Software Engineering from "
    "United Arab Emirates University.",
    "My most recent work was a consulting engagement forecasting housing completions for BC "
    "Housing, where I handled the data preparation, the forecasting models and the Power BI "
    "build. I'm looking for data analyst and data science roles.",
]
