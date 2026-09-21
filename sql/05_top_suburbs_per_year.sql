-- Q5: Which three suburbs led on sales volume each year, and how big was their share?
-- (Years are partial at the edges of the analysis window: 2023 = May-Dec, 2026 = Jan-Apr.)
-- Skills: ROW_NUMBER, window SUM for share-of-total, subquery filtering
WITH yearly AS (
    SELECT
        EXTRACT(year FROM sold_date)  AS sale_year,
        suburb,
        COUNT(*)                      AS sales
    FROM listings
    WHERE status = 'Sold'
      AND sold_date >= DATE '2023-05-01' AND sold_date < DATE '2026-05-01'   -- complete months only
    GROUP BY 1, 2
),
ranked AS (
    SELECT
        sale_year,
        suburb,
        sales,
        ROW_NUMBER() OVER (PARTITION BY sale_year ORDER BY sales DESC)  AS volume_rank,
        ROUND(100.0 * sales / SUM(sales) OVER (PARTITION BY sale_year), 1) AS share_of_year_pct
    FROM yearly
)
SELECT * FROM ranked
WHERE volume_rank <= 3
ORDER BY sale_year, volume_rank;
