# Average number of times that a keyword is mentioned in a restaurant's reviews
SELECT AVG((LENGTH(content) - LENGTH(REPLACE(content, 'burrito', ''))) / LENGTH('burrito')) AS cnt, business_id from review_mexican GROUP BY business_id order by cnt;

# Number of times that a keyword is mentioned in each review
SELECT (LENGTH(content) - LENGTH(REPLACE(content, 'burrito', ''))) / LENGTH('burrito') AS cnt, business_id from review_mexican order by cnt;

# Number of reviews for each restaurant in which a keyword is mentioned
select COUNT(review_id) AS nrev,business_id from review_mexican where content like '%burrito%' GROUP BY business_id ORDER BY nrev;

# Number of reviews for each restaurant
SELECT COUNT(review_id) AS nrev,business_id from review_mexican GROUP BY business_id ORDER BY nrev;

# Fraction of reviews that contain each keyword
SELECT nrev1, nrev2, nrev1 / nrev2 AS FRAC, id1 FROM
       (SELECT COUNT(r1.review_id) AS nrev1,r1.business_id AS id1 from review_mexican as r1 where content like '%burrito%' GROUP BY r1.business_id ORDER BY r1.business_id) AS NUMERATOR
        INNER JOIN
       (SELECT COUNT(r2.review_id) AS nrev2,r2.business_id AS id2 from review_mexican as r2 GROUP BY r2.business_id ORDER BY r2.business_id) AS DENOMINATOR
        ON (NUMERATOR.id1=DENOMINATOR.id2) 
    WHERE nrev2 > 10
    ORDER BY FRAC;



