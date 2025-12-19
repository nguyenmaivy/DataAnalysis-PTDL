import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

st.set_page_config(
    page_title="Dashboard Phòng Trọ TP.HCM",
    layout="wide"
)

# =========================
# LOAD DATA
# =========================
@st.cache_data
def load_data():
    df = pd.read_csv("results_hcm_clear.csv")

    df["posted_at"] = pd.to_datetime(df["posted_at"], errors="coerce")

    df = df.dropna(subset=["price_million", "area_m2"])
    df = df[(df["price_million"] > 0) & (df["area_m2"] > 0)]

    # ✅ GIÁ / m² (tạo 1 lần – dùng toàn app)
    df["price_per_m2"] = df["price_million"] / df["area_m2"]

    return df

df = load_data()

# =========================
# SIDEBAR FILTER
# =========================
st.sidebar.title("Bộ lọc dữ liệu")

districts = sorted(df["district_extracted"].dropna().unique())
selected_districts = st.sidebar.multiselect(
    "Chọn quận",
    districts,
    default=districts
)

price_range = st.sidebar.slider(
    "Khoảng giá (triệu/tháng)",
    float(df["price_million"].min()),
    float(df["price_million"].max()),
    (
        float(df["price_million"].quantile(0.05)),
        float(df["price_million"].quantile(0.95))
    )
)

area_range = st.sidebar.slider(
    "Diện tích (m²)",
    float(df["area_m2"].min()),
    float(df["area_m2"].max()),
    (
        float(df["area_m2"].quantile(0.05)),
        float(df["area_m2"].quantile(0.95))
    )
)

# =========================
# FILTER DATA
# =========================
df_f = df[
    (df["district_extracted"].isin(selected_districts)) &
    (df["price_million"].between(*price_range)) &
    (df["area_m2"].between(*area_range))
]

# =========================
# KPI
# =========================
st.title("Dashboard Phân Tích Phòng Trọ TP.HCM")

c1, c2, c3, c4 = st.columns(4)

c1.metric(" Số tin", f"{len(df_f):,}")
c2.metric(" Giá TB (triệu)", round(df_f["price_million"].mean(), 2))
c3.metric(" Diện tích TB (m²)", round(df_f["area_m2"].mean(), 1))
c4.metric(" Giá / m²", round(df_f["price_per_m2"].mean(), 2))

st.divider()

# =========================
# GIÁ THEO QUẬN
# =========================
st.subheader("Giá trung bình theo quận")

fig_price = px.bar(
    df_f.groupby("district_extracted", as_index=False)["price_million"].mean(),
    x="district_extracted",
    y="price_million",
    color="price_million"
)
st.plotly_chart(fig_price, use_container_width=True)

# =========================
# SCATTER + OUTLIER
# =========================
st.subheader(" Diện tích vs Giá (Outlier)")

q1 = df_f["price_million"].quantile(0.25)
q3 = df_f["price_million"].quantile(0.75)
iqr = q3 - q1
upper = q3 + 1.5 * iqr

df_f["outlier"] = df_f["price_million"] > upper

fig_scatter = px.scatter(
    df_f,
    x="area_m2",
    y="price_million",
    color="outlier",
    hover_data=["district_extracted"]
)
st.plotly_chart(fig_scatter, use_container_width=True)

# =========================
# TIME ANALYSIS
# =========================
st.subheader("Số tin theo thời gian")

df_time = df_f.dropna(subset=["posted_at"])
df_time["date"] = df_time["posted_at"].dt.date

fig_time = px.line(
    df_time.groupby("date").size().reset_index(name="count"),
    x="date",
    y="count"
)
st.plotly_chart(fig_time, use_container_width=True)

# =========================
# HEATMAP GIỜ ĐĂNG
# =========================
st.subheader(" Heatmap giờ đăng tin")

df_time["hour"] = df_time["posted_at"].dt.hour
df_time["weekday"] = df_time["posted_at"].dt.day_name()

heatmap = df_time.pivot_table(
    index="weekday",
    columns="hour",
    values="url",
    aggfunc="count"
)

fig_heat = px.imshow(heatmap, aspect="auto")
st.plotly_chart(fig_heat, use_container_width=True)

# =========================
# GỢI Ý GIÁ
# =========================
st.subheader(" Gợi ý giá hợp lý")

col1, col2 = st.columns(2)

with col1:
    input_district = st.selectbox("Quận", districts)

with col2:
    input_area = st.number_input("Diện tích (m²)", 10, 100, 25)

df_suggest = df[df["district_extracted"] == input_district]
median_price = df_suggest["price_per_m2"].median() * input_area

st.success(f" Giá đề xuất: **{round(median_price, 2)} triệu/tháng**")

# =========================
# TOP PHÒNG ĐÁNG THUÊ
# =========================
st.subheader("Top phòng đáng thuê")

df_rank = df_f.dropna(subset=["posted_at"]).copy()
df_rank["freshness"] = 1 / (
    (datetime.now() - df_rank["posted_at"]).dt.days + 1
)

df_rank["score"] = (
    df_rank["area_m2"] /
    df_rank["price_million"]
) * df_rank["freshness"]

st.dataframe(
    df_rank.sort_values("score", ascending=False)
    .head(10)[
        ["title", "price_million", "area_m2", "district_extracted", "score"]
    ]
)


# =========================
# TABLE
# =========================
st.subheader(" Danh sách tin")

st.dataframe(
    df_f[
        [
            "title",
            "price_million",
            "area_m2",
            "district_extracted",
            "price_per_m2",
            "posted_at"
        ]
    ]
)
