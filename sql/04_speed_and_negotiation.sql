-- Q4: How fast do properties sell, and how much room is there to negotiate?
-- Skills: DATE_DIFF, ratio metrics, CASE price bands, MEDIAN
SELECT
    suburb,
    CASE
        WHEN sold_price_zar <  1500000 THEN '1. Under R1.5m'
        WHEN sold_price_zar <  3000000 THEN '2. R1.5m - R3m'
        WHEN sold_price_zar <  5000000 THEN '3. R3m - R5m'
        ELSE                                '4. R5m+'
    END                                                             AS price_band,
    COUNT(*)                                                        AS sales,
    MEDIAN(DATE_DIFF('day', list_date, sold_date))                  AS median_days_on_market,
    ROUND(100.0 * (1 - MEDIAN(sold_price_zar / list_price_zar)), 1) AS median_discount_pct
FROM listings
WHERE status = 'Sold'
GROUP BY suburb, price_band
HAVING COUNT(*) >= 15
ORDER BY suburb, price_band;
