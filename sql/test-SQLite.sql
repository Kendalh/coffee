-- SQLite
select count(1) from coffee_bean;
select * from latest_data;



WITH latest AS (
    SELECT 
        provider,
        data_year,
        data_month
    FROM latest_data
    WHERE provider = '金粽'
)
SELECT 
    cb.*
FROM coffee_bean cb
INNER JOIN latest l
    ON cb.provider = l.provider
    AND cb.data_year = l.data_year
    AND cb.data_month = l.data_month
WHERE cb.country = '中国' AND cb.type = 'premium';
