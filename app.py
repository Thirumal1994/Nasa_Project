import streamlit as st
import pandas as pd
import numpy as np
import pymysql
from datetime import datetime

def get_connection():
    return pymysql.connect(
    host = '127.0.0.1',
    user='root',
    password='Thiru@1994',
    database = 'NASA_PROJECT')
    
def execute_query(query):
    conn = get_connection()
    df = pd.read_sql(query,conn)
    conn.commit()
    return df

    
queries = {
    "1. Count of asteroid approaches": """
        SELECT neo_reference_id, COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY neo_reference_id;
    """,
    "2. Average velocity per asteroid": """
        SELECT neo_reference_id, AVG(relative_velocity_kmph) AS avg_velocity
        FROM close_approach
        GROUP BY neo_reference_id;
    """,
    "3. Top 10 fastest asteroids": """
        SELECT neo_reference_id, MAX(relative_velocity_kmph) AS top_speed
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY top_speed DESC
        LIMIT 10;
    """,
    "4. Hazardous asteroids with >3 approaches": """
        SELECT a.id, a.name, COUNT(*) AS approach_count
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE a.is_potentially_hazardous_asteroid = TRUE
        GROUP BY a.id, a.name
        HAVING COUNT(*) > 3;
    """,
    "5. Month with most asteroid approaches": """
        SELECT MONTH(close_approach_date) AS month, COUNT(*) AS approach_count
        FROM close_approach
        GROUP BY MONTH(close_approach_date)
        ORDER BY approach_count DESC
        LIMIT 1;
    """,
    "6. Asteroid with fastest approach ever": """
        SELECT neo_reference_id, MAX(relative_velocity_kmph) AS max_speed
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY max_speed DESC
        LIMIT 1;
    """,
    "7. Sort by max estimated diameter": """
        SELECT id, name, estimated_diameter_max_km
        FROM asteroids
        ORDER BY estimated_diameter_max_km DESC;
    """,
    "8. Closest approach trend over time (most frequent asteroid)": """
        SELECT neo_reference_id, close_approach_date, miss_distance_km
        FROM close_approach
        WHERE neo_reference_id = (
            SELECT neo_reference_id
            FROM close_approach
            GROUP BY neo_reference_id
            ORDER BY COUNT(*) DESC
            LIMIT 1
        )
        ORDER BY close_approach_date ASC;
    """,
    "9. Closest approach for each asteroid": """
        SELECT c.neo_reference_id, a.name, c.close_approach_date, MIN(c.miss_distance_km) AS closest_distance
        FROM close_approach c
        JOIN asteroids a ON a.id = c.neo_reference_id
        GROUP BY c.neo_reference_id, a.name, c.close_approach_date;
    """,
    "10. Asteroids with velocity > 50,000 km/h": """
        SELECT DISTINCT a.id, a.name, c.relative_velocity_kmph
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.relative_velocity_kmph > 50000;
    """,
    "11. Monthly asteroid approach count": """
        SELECT MONTH(close_approach_date) AS month, COUNT(*) AS total_approaches
        FROM close_approach
        GROUP BY MONTH(close_approach_date)
        ORDER BY month;
    """,
    "12. Highest brightness (lowest magnitude)": """
        SELECT id, name, absolute_magnitude_h
        FROM asteroids
        ORDER BY absolute_magnitude_h ASC
        LIMIT 1;
    """,
    "13. Hazardous vs Non-Hazardous": """
        SELECT is_potentially_hazardous_asteroid, COUNT(*) AS total
        FROM asteroids
        GROUP BY is_potentially_hazardous_asteroid;
    """,
    "14. Asteroids passing closer than the Moon (< 1 LD)": """
        SELECT a.name, c.close_approach_date, c.miss_distance_lunar
        FROM asteroids a
        JOIN close_approach c ON a.id = c.neo_reference_id
        WHERE c.miss_distance_lunar < 1;
    """,
    "15. Asteroids that came within 0.05 AU": """
        SELECT name, close_approach_date, astronomical
        FROM asteroids 
        JOIN close_approach  ON id = neo_reference_id
        WHERE astronomical < 0.05;
    """,
    "16. Bottom 10 fastest asteroids": """
        SELECT neo_reference_id, MAX(relative_velocity_kmph) AS bottom_speed
        FROM close_approach
        GROUP BY neo_reference_id
        ORDER BY bottom_speed ASC
        LIMIT 10;
    """,
    "17. show the asteroid table":"""
         SELECT * from asteroids;
     """,
    "18. show the Closeapproach table":"""
         SELECT * from close_approach;
     """,
    "19. Sort by min estimated diameter": """
        SELECT id, name, estimated_diameter_min_km
        FROM asteroids
        ORDER BY estimated_diameter_min_km ASC;
    """,
    "20. Count of unique asteroids by orbiting body":"""
         SELECT orbiting_body, COUNT(DISTINCT neo_reference_id) AS unique_asteroids
         FROM close_approach
         GROUP BY orbiting_body
         ORDER BY unique_asteroids DESC;
     """    
}

st.set_page_config(page_title="NASA NEO Dashboard", layout="wide")
st.title("🚀 NASA Near-Earth Object (NEO) Tracking Insights")
st.caption("Asteroids and close approach")

st.sidebar.header("🚀Asteroids approach")

query_title = st.sidebar.selectbox("📊 Choose a SQL Query", list(queries.keys()))




if st.button("Run query"):
    with st.spinner("Fetching data..."):
        df = execute_query(queries[query_title])
        st.dataframe(df)

st.markdown("Use the filters below to explore asteroid data from NASA's Near-Earth Object (NEO) API.")


st.subheader("🎛️ Apply Filters")

col1, col2, col3 = st.columns(3)

with col1:
    date_range = st.date_input("📅 Close Approach Date", [])
    hazard_status = st.selectbox("☄️ Hazardous State", ["Any", "True", "False"])

with col2:
    rel_velocity = st.slider("⚡ Minimum Relative Velocity (km/h)", 0, 100000, 25000)
    diameter_min = st.slider("🪨 Min Estimated Diameter (km)", 0.0, 10.0, 0.5)
    diameter_max = st.slider("🪨 Max Estimated Diameter (km)", 0.0, 10.0, 0.5)

with col3:
    max_au = st.slider("🌌 Max Distance (AU)", 0.00, 1.00, 0.05)
    max_ld = st.slider("🌑 Max Distance (Lunar Units)", 0.0, 10.0, 200.00)

base_query = """
    SELECT a.name,
           a.estimated_diameter_min_km,
           a.estimated_diameter_max_km,
           a.is_potentially_hazardous_asteroid,
           c.close_approach_date,
           c.relative_velocity_kmph,
           c.astronomical,
           c.miss_distance_km,
           c.miss_distance_lunar
    FROM asteroids a
    JOIN close_approach c ON a.id = c.neo_reference_id
    WHERE c.relative_velocity_kmph >= %s
      AND a.estimated_diameter_min_km >= %s
      AND a.estimated_diameter_max_km >= %s
      AND c.astronomical <= %s
      AND c.miss_distance_lunar <= %s
"""

params = [rel_velocity, diameter_min, diameter_max, max_au, max_ld]

if len(date_range) == 2:
    base_query += " AND c.close_approach_date BETWEEN %s AND %s"
    params += [str(date_range[0]), str(date_range[1])]

if hazard_status == "True":
    base_query += " AND a.is_potentially_hazardous_asteroid = TRUE"
elif hazard_status == "False":
    base_query += " AND a.is_potentially_hazardous_asteroid = FALSE"

base_query += " ORDER BY c.relative_velocity_kmph DESC"



with get_connection() as conn:
    
    df = pd.read_sql(base_query, conn, params=params)
    st.success(f"🔎 {len(df)} records found")
    st.dataframe(df, use_container_width=True)






    




