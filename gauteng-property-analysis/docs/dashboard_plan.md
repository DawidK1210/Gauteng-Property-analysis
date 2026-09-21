# Dashboard plan (Power BI or Tableau Public)

Connect to the CSVs in `/outputs`. Build three pages, each answering one question.

**Page 1: Market overview** (from `01_suburb_overview.csv`, `02_price_trend.csv`)
- KPI cards: total sales, median sold price, median price per m²
- Line chart: monthly median price per m² with the 3-month moving average
- Bar chart: median price per m² by suburb, sorted
- Slicers: property type, year

**Page 2: Value screening** (from `03_below_market_suburbs.csv`)
- Bar chart: % vs market by suburb, one panel per property type
- Table: suburb, sales, price per m², % vs market, conditional formatting on % vs market
- A text box stating the limitation (below market is not the same as undervalued)

**Page 3: Speed and negotiation** (from `04_speed_and_negotiation.csv`)
- Heatmap or matrix: suburb × price band, coloured by median days on market
- Bar chart: median discount off asking price by suburb

**Publishing:** Tableau Public is free and gives a shareable link. Power BI Desktop is free, but sharing needs a Power BI account; a PDF export and screenshots in the README work as a fallback.
