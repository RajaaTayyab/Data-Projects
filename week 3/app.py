import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ast
import warnings
warnings.filterwarnings("ignore")

st.set_page_config(
    page_title="CineMetrics | Cinema Intelligence",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Matplotlib theme 
PLOT_BG  = "#080C14"
GRID_CLR = "#1E2D45"
TEXT_CLR = "#8A9BBF"
RED      = "#E50914"
GOLD     = "#F5C518"
TEAL     = "#00B4D8"

plt.rcParams.update({
    "figure.facecolor": PLOT_BG,
    "axes.facecolor":   PLOT_BG,
    "axes.edgecolor":   GRID_CLR,
    "axes.labelcolor":  TEXT_CLR,
    "xtick.color":      TEXT_CLR,
    "ytick.color":      TEXT_CLR,
    "grid.color":       GRID_CLR,
    "grid.linewidth":   0.5,
    "text.color":       TEXT_CLR,
    "font.family":      "sans-serif",
})

# Data loading 
@st.cache_data
def load_data():
    df = pd.read_csv("tmdb_5000_movies.csv")

    #fixing 0s
    df["release_date"] = pd.to_datetime(df["release_date"], errors="coerce")
    df["release_year"] = df["release_date"].dt.year
    df = df.dropna(subset=["release_year"])
    df["release_year"] = df["release_year"].astype(int)

    #ckeaning dataset
    df["budget_clean"]  = df["budget"].where(df["budget"] > 100_000)
    df["revenue_clean"] = df["revenue"].where(df["revenue"] > 100_000)
    df["roi"]     = ((df["revenue_clean"] - df["budget_clean"]) / df["budget_clean"] * 100).round(1)
    df["profit_m"] = ((df["revenue_clean"] - df["budget_clean"]) / 1e6).round(1)

#extracting genres
    def parse_genres(g):
        try:
            return [x["name"] for x in ast.literal_eval(g)]
        except Exception:
            return []

    df["genre_list"]    = df["genres"].apply(parse_genres)
    df["primary_genre"] = df["genre_list"].apply(lambda g: g[0] if g else "Unknown")
    df["decade"]        = (df["release_year"] // 10 * 10).astype(str) + "s"
    return df

df = load_data()

# ─ Sidebar 
with st.sidebar:
    st.title("CineMetrics")
    st.caption("Cinema Intelligence Dashboard")
    st.divider()

    st.subheader("Era")
    year_range = st.slider(
        "Release years",
        int(df["release_year"].min()), 2010, (1990, 2024),
        label_visibility="collapsed"
    )

    st.subheader("Minimum Rating")
    min_rating = st.select_slider(
        "Min rating",
        options=[0, 2, 4, 6, 7, 8, 9, 10],
        value=6,
        label_visibility="collapsed"
    )

    genres_available = sorted({g for lst in df["genre_list"] for g in lst if g != "Unknown"})
    st.subheader("Genres")
    selected_genres = st.multiselect(
        "Select genres",
        genres_available,
        default=[],
        placeholder="All genres",
        label_visibility="collapsed"
    )

    st.subheader("Sort Top Movies By")
    sort_by = st.radio(
        "Sort by",
        ["Popularity", "Rating", "Revenue", "ROI"],
        horizontal=True,
        label_visibility="collapsed"
    )

    st.divider()
    st.caption("Data: TMDB 5000 Movies · Built with Streamlit")

# Filtering 
fdf = df[
    (df["release_year"] >= year_range[0]) &
    (df["release_year"] <= year_range[1]) &
    (df["vote_average"] >= min_rating)
]
if selected_genres:
    fdf = fdf[fdf["genre_list"].apply(lambda g: any(x in g for x in selected_genres))]

# Header 
st.title(f"The {year_range[0]}–{year_range[1]} Era")
genre_label = "All genres" if not selected_genres else ", ".join(selected_genres)
st.caption(f"Analysing {len(fdf):,} films · Ratings ≥ {min_rating} · {genre_label}")

if fdf.empty:
    st.warning("No movies match your filters. Try loosening the criteria.")
    st.stop()

# ─KPI Metrics 
avg_rating  = fdf["vote_average"].mean()
avg_budget  = fdf["budget_clean"].mean() / 1e6
avg_revenue = fdf["revenue_clean"].mean() / 1e6
avg_roi     = fdf["roi"].mean()
all_avg     = df[
    (df["release_year"] >= year_range[0]) &
    (df["release_year"] <= year_range[1])
]["vote_average"].mean()

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Films Analysed",  f"{len(fdf):,}")
k2.metric("Avg IMDb Rating", f"{avg_rating:.2f}", f"{avg_rating - all_avg:+.2f} vs era avg")
k3.metric("Avg Budget",      f"${avg_budget:.0f}M"  if not pd.isna(avg_budget)  else "N/A")
k4.metric("Avg Box Office",  f"${avg_revenue:.0f}M" if not pd.isna(avg_revenue) else "N/A")
k5.metric("Avg ROI",         f"{avg_roi:.0f}%"      if not pd.isna(avg_roi)     else "N/A")

st.divider()

# ─ Row 1: Trend + Genre 
col_a, col_b = st.columns([3, 2], gap="large")

with col_a:
    st.subheader("Popularity Over Time")

    yearly = fdf.groupby("release_year").agg(
        avg_pop=("popularity", "mean"),
        avg_rating=("vote_average", "mean"),
        count=("title", "count")
    ).reset_index()

    fig, ax1 = plt.subplots(figsize=(10, 4))
    ax1.fill_between(yearly["release_year"], yearly["avg_pop"], alpha=0.15, color=RED)
    ax1.plot(yearly["release_year"], yearly["avg_pop"], color=RED, linewidth=2.5, label="Avg Popularity")
    ax1.set_ylabel("Popularity Score", color=RED, fontsize=9)
    ax1.tick_params(axis="y", colors=RED)

    ax2 = ax1.twinx()
    ax2.plot(yearly["release_year"], yearly["avg_rating"], color=GOLD, linewidth=1.8,
             linestyle="--", alpha=0.85, label="Avg Rating")
    ax2.set_ylabel("IMDb Rating", color=GOLD, fontsize=9)
    ax2.tick_params(axis="y", colors=GOLD)
    ax2.set_ylim(0, 10)
    ax2.set_facecolor(PLOT_BG)

    ax1.set_xlabel("Year", fontsize=9)
    ax1.grid(axis="y", alpha=0.3)
    ax1.set_xlim(yearly["release_year"].min(), yearly["release_year"].max())

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc="upper left",
               framealpha=0.1, fontsize=8, labelcolor="white")
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()

with col_b:
    st.subheader("Genre Distribution")

    genre_counts = pd.Series(
        [g for lst in fdf["genre_list"] for g in lst]
    ).value_counts().head(8)

    fig, ax = plt.subplots(figsize=(6, 4))
    colors = [RED if i == 0 else f"#{max(30, 229 - i*28):02X}1E{max(14, 20):02X}"
              for i in range(len(genre_counts))]
    bars = ax.barh(genre_counts.index[::-1], genre_counts.values[::-1],
                   color=colors[::-1], height=0.65)
    for bar, val in zip(bars, genre_counts.values[::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(val), va="center", fontsize=8, color=TEXT_CLR)
    ax.set_xlabel("Number of Films", fontsize=9)
    ax.grid(axis="x", alpha=0.3)
    ax.spines[["top", "right", "left"]].set_visible(False)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()

st.divider()

# ─ Row 2: Scatter + ROI by genre 
col_c, col_d = st.columns(2, gap="large")

with col_c:
    st.subheader("Budget vs Box Office")

    scatter_df = fdf.dropna(subset=["budget_clean", "revenue_clean"]).copy()
    scatter_df = scatter_df[scatter_df["budget_clean"] > 0]

    profitable = scatter_df[scatter_df["revenue_clean"] >= scatter_df["budget_clean"]]
    loss       = scatter_df[scatter_df["revenue_clean"] <  scatter_df["budget_clean"]]

    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(loss["budget_clean"] / 1e6, loss["revenue_clean"] / 1e6,
               alpha=0.4, s=18, color="#FF4444", label="Loss", zorder=3)
    ax.scatter(profitable["budget_clean"] / 1e6, profitable["revenue_clean"] / 1e6,
               alpha=0.5, s=18, color=TEAL, label="Profitable", zorder=3)

    max_val = max(scatter_df["budget_clean"].max(), scatter_df["revenue_clean"].max()) / 1e6
    ax.plot([0, max_val], [0, max_val], "--", color=GOLD, linewidth=1, alpha=0.6, label="Break-even")
    ax.set_xlabel("Production Budget ($M)", fontsize=9)
    ax.set_ylabel("Box Office Revenue ($M)", fontsize=9)
    ax.legend(framealpha=0.1, fontsize=8, labelcolor="white")
    ax.grid(alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    st.pyplot(fig)
    plt.close()

with col_d:
    st.subheader("Avg ROI by Genre")

    genre_roi_rows = [
        {"genre": g, "roi": row["roi"]}
        for _, row in fdf.dropna(subset=["roi"]).iterrows()
        for g in row["genre_list"]
    ]

    if genre_roi_rows:
        genre_roi = (
            pd.DataFrame(genre_roi_rows)
            .groupby("genre")["roi"]
            .median()
            .sort_values(ascending=False)
            .head(8)
        )
        fig, ax = plt.subplots(figsize=(7, 4.5))
        bar_colors = [GOLD if v > 0 else "#FF4444" for v in genre_roi.values]
        bars = ax.bar(genre_roi.index, genre_roi.values, color=bar_colors, width=0.6)
        ax.axhline(0, color=TEXT_CLR, linewidth=0.8, alpha=0.5)
        ax.set_ylabel("Median ROI (%)", fontsize=9)
        ax.set_xlabel("Genre", fontsize=9)
        plt.xticks(rotation=35, ha="right", fontsize=8)
        for bar, val in zip(bars, genre_roi.values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 5,
                    f"{val:.0f}%", ha="center", fontsize=7.5, color=TEXT_CLR)
        ax.grid(axis="y", alpha=0.2)
        ax.spines[["top", "right"]].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close()
    else:
        st.info("Not enough financial data for this selection.")

st.divider()

#  Row 3: Top Movies 
col_e = st.columns([1])[0]
sort_col_map = {
    "Popularity": "popularity",
    "Rating":     "vote_average",
    "Revenue":    "revenue_clean",
    "ROI":        "roi",
}
sort_col = sort_col_map[sort_by]

with col_e:
    st.subheader(f"Top 10 by {sort_by}")

    top10 = (
        fdf.dropna(subset=[sort_col])
        .nlargest(10, sort_col)[["title", sort_col, "release_year", "vote_average"]]
        .reset_index(drop=True)
    )

    for i, row in top10.iterrows():
        val = row[sort_col]
        if sort_by == "Revenue":   val_str = f"${val/1e6:.0f}M"
        elif sort_by == "ROI":     val_str = f"{val:.0f}%"
        else:                      val_str = f"{val:.1f}"

        with st.container(border=True):
            rank_col, info_col = st.columns([1, 6])
            rank_col.markdown(f"**#{i+1}**")
            info_col.write(f"**{row['title']}**")
            info_col.caption(f"{int(row['release_year'])} · ⭐ {row['vote_average']:.1f} · {sort_by}: {val_str}")

st.divider()

# Raw data 
with st.expander("View Filtered Dataset"):
    display_cols = ["title", "release_year", "primary_genre", "vote_average",
                    "popularity", "budget_clean", "revenue_clean", "roi"]
    display_df = fdf[display_cols].copy()
    display_df.columns = ["Title", "Year", "Genre", "Rating",
                           "Popularity", "Budget ($)", "Revenue ($)", "ROI (%)"]
    display_df["Budget ($)"]  = display_df["Budget ($)"].apply(
        lambda x: f"${x/1e6:.1f}M" if pd.notna(x) else "—")
    display_df["Revenue ($)"] = display_df["Revenue ($)"].apply(
        lambda x: f"${x/1e6:.1f}M" if pd.notna(x) else "—")
    display_df["ROI (%)"]     = display_df["ROI (%)"].apply(
        lambda x: f"{x:.0f}%" if pd.notna(x) else "—")
    display_df["Rating"]      = display_df["Rating"].round(1)
    st.dataframe(
        display_df.sort_values("Popularity", ascending=False).reset_index(drop=True),
        use_container_width=True,
        height=320
    )

# ── Footer 
st.divider()
st.caption("CINEMETRICS  · TMDB 5000 DATASET  · BY TAYYAB JANJUA")