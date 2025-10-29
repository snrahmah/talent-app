WITH benchmark AS (
  SELECT DISTINCT employee_id
  FROM `rakamin-476503.tgv_dataset.tgv_score`
  WHERE employee_id IN UNNEST([{{benchmark_ids}}])
),
baseline AS (
  SELECT tgv, APPROX_QUANTILES(adjusted_score, 100)[OFFSET(50)] AS baseline_score
  FROM `rakamin-476503.tgv_dataset.tgv_score`
  WHERE employee_id IN (SELECT employee_id FROM benchmark)
  GROUP BY tgv
),
match_rate AS (
  SELECT a.employee_id, a.tgv, a.adjusted_score, b.baseline_score,
         SAFE_DIVIDE(a.adjusted_score, b.baseline_score)*100 AS tgv_match_rate
  FROM `rakamin-476503.tgv_dataset.tgv_score` a
  LEFT JOIN baseline b USING (tgv)
),
weighted AS (
  SELECT m.employee_id, m.tgv, m.tgv_match_rate, w.weight
  FROM match_rate m
  LEFT JOIN `rakamin-476503.tgv_dataset.weights` w USING (tgv)
),
final AS (
  SELECT employee_id, SUM(tgv_match_rate*weight)/SUM(weight) AS final_match_rate
  FROM weighted
  GROUP BY employee_id
)
SELECT * FROM final ORDER BY final_match_rate DESC;
