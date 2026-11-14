-- =====================================================================
-- Retail Sales Analytics -- SQL Portfolio Queries
-- Database: superstore.db (normalized from the Superstore retail dataset)
-- Demonstrates: joins, CTEs, window functions, cohort analysis, RFM
-- Author: Mo Maghaireh
-- =====================================================================

-- Q1. Yearly revenue, profit, and YoY growth (window functions)
WITH yearly AS (
  SELECT strftime('%Y', o.order_date) AS year,
         ROUND(SUM(i.sales), 0)  AS revenue,
         ROUND(SUM(i.profit), 0) AS profit,
         COUNT(DISTINCT o.order_id) AS orders
  FROM orders o JOIN order_items i USING (order_id)
  GROUP BY 1
)
SELECT year, revenue, profit, orders,
       ROUND(100.0 * (revenue - LAG(revenue) OVER (ORDER BY year))
             / LAG(revenue) OVER (ORDER BY year), 1) AS yoy_revenue_pct
FROM yearly;

-- Q2. Top 10 sub-categories by profit, with profit margin and revenue rank
SELECT p.category, p.sub_category,
       ROUND(SUM(i.sales), 0)  AS revenue,
       ROUND(SUM(i.profit), 0) AS profit,
       ROUND(100.0 * SUM(i.profit) / SUM(i.sales), 1) AS margin_pct,
       RANK() OVER (ORDER BY SUM(i.sales) DESC) AS revenue_rank
FROM order_items i JOIN products p USING (product_id)
GROUP BY 1, 2
ORDER BY profit DESC
LIMIT 10;

-- Q3. Loss-making sub-categories: where discounting destroys profit
SELECT p.sub_category,
       ROUND(AVG(i.discount) * 100, 1) AS avg_discount_pct,
       ROUND(SUM(i.profit), 0) AS total_profit,
       COUNT(*) AS line_items
FROM order_items i JOIN products p USING (product_id)
GROUP BY 1
HAVING SUM(i.profit) < 0
ORDER BY total_profit;

-- Q4. Monthly cohort retention: % of each signup cohort ordering again
WITH first_order AS (
  SELECT customer_id, MIN(strftime('%Y-%m', order_date)) AS cohort
  FROM orders GROUP BY 1
),
activity AS (
  SELECT DISTINCT o.customer_id, f.cohort,
         (strftime('%Y', o.order_date) - substr(f.cohort,1,4)) * 12
         + (strftime('%m', o.order_date) - substr(f.cohort,6,2)) AS months_since
  FROM orders o JOIN first_order f USING (customer_id)
)
SELECT substr(cohort, 1, 4) AS cohort_year,
       COUNT(DISTINCT CASE WHEN months_since = 0  THEN customer_id END) AS new_customers,
       ROUND(100.0 * COUNT(DISTINCT CASE WHEN months_since BETWEEN 1  AND 12 THEN customer_id END)
             / COUNT(DISTINCT CASE WHEN months_since = 0 THEN customer_id END), 1) AS retained_12m_pct
FROM activity
GROUP BY 1;

-- Q5. RFM segmentation (recency / frequency / monetary quintiles)
WITH rfm AS (
  SELECT o.customer_id,
         CAST(julianday((SELECT MAX(order_date) FROM orders)) - julianday(MAX(o.order_date)) AS INT) AS recency_days,
         COUNT(DISTINCT o.order_id) AS frequency,
         ROUND(SUM(i.sales), 0) AS monetary
  FROM orders o JOIN order_items i USING (order_id)
  GROUP BY 1
),
scored AS (
  SELECT *,
         NTILE(5) OVER (ORDER BY recency_days DESC) AS r,
         NTILE(5) OVER (ORDER BY frequency)          AS f,
         NTILE(5) OVER (ORDER BY monetary)           AS m
  FROM rfm
)
SELECT CASE
         WHEN r >= 4 AND f >= 4 THEN 'Champions'
         WHEN r >= 4 AND f <= 2 THEN 'New / Promising'
         WHEN r <= 2 AND f >= 4 THEN 'At Risk (was loyal)'
         WHEN r <= 2 AND f <= 2 THEN 'Lost'
         ELSE 'Regular'
       END AS segment,
       COUNT(*) AS customers,
       ROUND(AVG(monetary), 0) AS avg_lifetime_sales,
       ROUND(AVG(recency_days), 0) AS avg_days_since_order
FROM scored
GROUP BY 1
ORDER BY customers DESC;

-- Q6. Average shipping lag by ship mode and region (operational KPI)
SELECT ship_mode, region,
       ROUND(AVG(julianday(ship_date) - julianday(order_date)), 1) AS avg_ship_days,
       COUNT(*) AS orders
FROM orders
GROUP BY 1, 2
ORDER BY ship_mode, region;

-- Q7. Top 5 customers per region by revenue (window function + filter)
WITH cust_rev AS (
  SELECT o.region, c.customer_name, ROUND(SUM(i.sales), 0) AS revenue,
         ROW_NUMBER() OVER (PARTITION BY o.region ORDER BY SUM(i.sales) DESC) AS rn
  FROM orders o
  JOIN order_items i USING (order_id)
  JOIN customers c USING (customer_id)
  GROUP BY 1, 2
)
SELECT region, customer_name, revenue FROM cust_rev WHERE rn <= 5;
