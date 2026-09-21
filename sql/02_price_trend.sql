-- Q2: Is the market rising? Monthly median price per m2 with a 3-month
-- moving average and year-on-year change.
-- Skills: CTE, window functions (AVG OVER, LAG), date truncation
WITH monthly AS (
    SELECT
        DATE_TRUNC('month', sold_date)                 AS sale_month,
        COUNT(*)                                       AS sales,
        MEDIAN(sold_price_zar / floor_size_m2)         AS median_ppm2
    FROM listings
    WHERE status = 'Sold'
      AND floor_size_m2 IS NOT NULL
      -- complete months only: the first months after the data starts and the
      -- last months before it ends contain only quick sales and would distort the trend
      AND sold_date >= DATE '2023-05-01' AND sold_date < DATE '2026-05-01'
    GROUP BY 1
)
SELECT
    sale_month,
    sales,
    ROUND(median_ppm2)                                                         AS median_ppm2,
    ROUND(AVG(median_ppm2) OVER (ORDER BY sale_month
                                 ROWS BETWEEN 2 PRECEDING AND CURRENT ROW))    AS moving_avg_3m,
    ROUND(100.0 * (median_ppm2 / LAG(median_ppm2, 12) OVER (ORDER BY sale_month) - 1), 1) AS yoy_change_pct
FROM monthly
ORDER BY sale_month;
