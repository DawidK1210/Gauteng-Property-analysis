-- Q1: How does each suburb compare on volume, price and price per m2?
-- Skills: aggregation, median, filtering NULLs, CASE
SELECT
    suburb,
    COUNT(*)                                                       AS sales,
    ROUND(MEDIAN(sold_price_zar))                                  AS median_sold_price,
    ROUND(MEDIAN(sold_price_zar / floor_size_m2))                  AS median_price_per_m2,
    ROUND(MEDIAN(sold_price_zar / floor_size_m2)
          FILTER (WHERE property_type = 'House'))                  AS median_ppm2_house,
    ROUND(MEDIAN(sold_price_zar / floor_size_m2)
          FILTER (WHERE property_type = 'Apartment'))              AS median_ppm2_apartment
FROM listings
WHERE status = 'Sold'
  AND floor_size_m2 IS NOT NULL
GROUP BY suburb
ORDER BY median_price_per_m2 DESC;
