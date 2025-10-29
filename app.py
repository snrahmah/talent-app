# app.py
import streamlit as st
from google.cloud import bigquery
import pandas as pd
import plotly.express as px
from google.oauth2 import service_account


# Load BigQuery credentials from Streamlit Secrets

try:
    key_dict = st.secrets["google"] 
    credentials = service_account.Credentials.from_service_account_info(key_dict)
    client = bigquery.Client(credentials=credentials, project=key_dict["project_id"])
except Exception as e:
    st.error("Error loading BigQuery credentials. Ensure the Secrets has been set correctly.")
    st.stop()


# Streamlit UI

st.set_page_config(page_title="AI Talent Match", layout="wide")
st.title("AI Talent Match App")

st.sidebar.header("Benchmark Inputs")
benchmark_ids = st.sidebar.text_input("Enter benchmark employee IDs (comma-separated)", "312,335,175")
run_btn = st.sidebar.button("Run Matching")

if run_btn:
    benchmark_list = [int(x.strip()) for x in benchmark_ids.split(',') if x.strip().isdigit()]

    if len(benchmark_list) == 0:
        st.error("Please input at least one valid employee ID.")
    else:
        benchmark_str = ",".join(map(str, benchmark_list))

        query = f"""WITH benchmark AS (
          SELECT DISTINCT employee_id
          FROM UNNEST([{benchmark_str}]) AS employee_id
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
          SELECT employee_id,
                 SUM(tgv_match_rate*weight)/SUM(weight) AS final_match_rate
          FROM weighted
          GROUP BY employee_id
        )
        SELECT * FROM final ORDER BY final_match_rate DESC"""

        df = client.query(query).to_dataframe()

        st.subheader("Ranked Talent List")
        st.dataframe(df)

        fig = px.histogram(df, x='final_match_rate', nbins=20,
                           title='Distribution of Final Match Rate')
        st.plotly_chart(fig, use_container_width=True)

        if not df.empty:
            selected_emp = st.selectbox("Select Employee to view TGV breakdown:", df["employee_id"])
            breakdown_query = f"""WITH benchmark AS (
              SELECT DISTINCT employee_id
              FROM UNNEST([{benchmark_str}]) AS employee_id
            ),
            baseline AS (
              SELECT tgv, APPROX_QUANTILES(adjusted_score, 100)[OFFSET(50)] AS baseline_score
              FROM `rakamin-476503.tgv_dataset.tgv_score`
              WHERE employee_id IN (SELECT employee_id FROM benchmark)
              GROUP BY tgv
            ),
            match_rate AS (
              SELECT a.employee_id, a.tgv, SAFE_DIVIDE(a.adjusted_score, b.baseline_score)*100 AS tgv_match_rate
              FROM `rakamin-476503.tgv_dataset.tgv_score` a
              LEFT JOIN baseline b USING (tgv)
              WHERE a.employee_id = {selected_emp}
            )
            SELECT tgv, ROUND(tgv_match_rate,2) AS tgv_match_rate
            FROM match_rate
            ORDER BY tgv_match_rate DESC"""

            df_breakdown = client.query(breakdown_query).to_dataframe()
            fig2 = px.bar(df_breakdown, x='tgv', y='tgv_match_rate', text='tgv_match_rate',
                          title=f"TGV Breakdown for Employee {selected_emp}")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No results found. Please check your input IDs.")
else:
    st.info("Enter benchmark employee IDs in the sidebar, then click 'Run Matching'.")
