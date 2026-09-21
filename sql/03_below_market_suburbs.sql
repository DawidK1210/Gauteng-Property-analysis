-- Q3: Which suburbs sell below the market price per m2 for the same property type?
-- (Below-market is a screening signal, not proof of undervaluation: it ignores
--  condition, stand size, security estates, etc. Say so in your write-up.)
-- Skills: multiple CTEs, joins, RANK() OVER (PARTITION BY ...), HAVING
WITH suburb_stats AS (
    SELECT
        suburb,
        property_type,
        COUNT(*)                                AS sales,
        MEDIAN(sold_price_zar / floor_size_m2)  AS suburb_ppm2
    FROM listings
    WHERE status = 'Sold' AND floor_size_m2 IS NOT NULL
    GROUP BY suburb, property_type
    HAVING COUNT(*) >= 30                        -- ignore thin samples
),
market AS (
    SELECT
        property_type,
        MEDIAN(sold_price_zar / floor_size_m2)  AS market_ppm2
    FROM listings
    WHERE status = 'Sold' AND floor_size_m2 IS NOT NULL
    GROUP BY property_type
)
SELECT
    s.property_type,
    s.suburb,
    s.sales,
    ROUND(s.suburb_ppm2)                                          AS suburb_ppm2,
    ROUND(m.market_ppm2)                                          AS market_ppm2,
    ROUND(100.0 * (s.suburb_ppm2 / m.market_ppm2 - 1), 1)         AS pct_vs_market,
    RANK() OVER (PARTITION BY s.property_type ORDER BY s.suburb_ppm2) AS cheapest_rank
FROM suburb_stats s
JOIN market m USING (property_type)
ORDER BY s.property_type, cheapest_rank;
