"""Streamlit dashboard over the football API.

Run the API first (uvicorn src.api.main:app), then:
    streamlit run src/dashboard/app.py

The API base URL can be changed with the FOOTBALL_API_URL environment
variable.
"""

import os

import pandas as pd
import requests
import streamlit as st

API_URL = os.environ.get("FOOTBALL_API_URL", "http://127.0.0.1:8000")

LEADERBOARD_METRICS = {
    "Goals": "goals",
    "Assists": "assists",
    "Expected goals (xG)": "xg",
    "Shots": "shots",
    "Progressive passes": "progressive_passes",
    "Tackles won": "tackles_won",
    "Interceptions": "interceptions",
    "Minutes played": "minutes_played",
}

COMPARE_METRICS = [
    "goals_per_90", "assists_per_90", "shots_per_90", "xg_per_90",
    "progressive_passes_per_90", "tackles_per_90", "interceptions_per_90",
]


@st.cache_data(ttl=60)
def api_get(path, params=None):
    """GET a path from the API and return the decoded JSON."""

    response = requests.get(f"{API_URL}{path}", params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def show_api_error(error):
    st.error(
        f"Could not reach the API at {API_URL}. Start it with "
        f"`uvicorn src.api.main:app` and make sure the pipeline has been run.\n\n"
        f"Details: {error}"
    )


def matches_page():
    st.header("Matches")

    team = st.text_input("Filter by team")
    matches = api_get("/matches", {"team": team or None, "limit": 500})

    if not matches:
        st.info("No matches found.")
        return

    df = pd.DataFrame(matches)
    df["result"] = (
        df["home_team"] + " " + df["home_score"].astype(str) + " - "
        + df["away_score"].astype(str) + " " + df["away_team"]
    )

    st.dataframe(
        df[["match_date", "result", "home_xg", "away_xg",
            "home_pass_share_pct", "away_pass_share_pct"]],
        hide_index=True,
        use_container_width=True,
    )

    selected = st.selectbox(
        "Match detail",
        df["match_id"],
        format_func=lambda i: df.loc[df["match_id"] == i, "result"].iloc[0],
    )

    detail = api_get(f"/matches/{selected}")
    teams = pd.DataFrame(detail["teams"]).set_index("team")

    st.subheader("Team comparison")
    st.dataframe(
        teams[["goals", "shots", "shots_on_target", "xg",
               "pass_accuracy_pct", "pass_share_pct",
               "possessions", "pressures", "fouls_committed"]].T,
        use_container_width=True,
    )


def players_page():
    st.header("Player leaderboard")

    left, middle, right = st.columns(3)
    label = left.selectbox("Rank by", list(LEADERBOARD_METRICS))
    min_minutes = middle.slider("Minimum minutes", 0, 600, 180, step=30)
    team = right.text_input("Team contains")

    metric = LEADERBOARD_METRICS[label]

    players = api_get("/players", {
        "sort_by": metric,
        "min_minutes": min_minutes,
        "team": team or None,
        "limit": 20,
    })

    if not players:
        st.info("No players match those filters.")
        return

    df = pd.DataFrame(players)

    st.bar_chart(df, x="player_name", y=metric, sort=f"-{metric}")

    st.dataframe(
        df[["player_name", "team", "appearances", "minutes_played", "goals",
            "assists", "xg", "pass_completion_pct", "progressive_passes",
            "tackles_won", "interceptions"]],
        hide_index=True,
        use_container_width=True,
    )


def compare_page():
    st.header("Compare players")

    candidates = api_get("/players", {"min_minutes": 90, "limit": 500})
    names = {p["player_id"]: f"{p['player_name']} ({p['team']})"
             for p in candidates}

    chosen = st.multiselect(
        "Choose 2 to 5 players",
        list(names),
        format_func=lambda i: names[i],
        max_selections=5,
    )

    if len(chosen) < 2:
        st.info("Select at least two players.")
        return

    comparison = api_get("/players/compare", {"ids": chosen})

    rows = {}
    for player in comparison:
        rows[player["player_name"]] = {
            **{metric: player["per_90"][metric] for metric in COMPARE_METRICS},
            "minutes_played": player["minutes_played"],
            "pass_completion_pct": player["pass_completion_pct"],
        }

    df = pd.DataFrame(rows)

    st.caption("Rate statistics are per 90 minutes played.")
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df.loc[COMPARE_METRICS])


def teams_page():
    st.header("Team statistics")

    teams = api_get("/teams")
    names = {t["team_id"]: t["team"] for t in teams}

    team_id = st.selectbox("Team", list(names), format_func=lambda i: names[i])

    stats = api_get(f"/teams/{team_id}/statistics")
    totals = stats["totals"]

    columns = st.columns(4)
    columns[0].metric("Matches", totals["matches"])
    columns[1].metric("Goals for / against",
                      f"{totals['goals']} / {totals['goals_against']}")
    columns[2].metric("xG for / against",
                      f"{totals['xg']:.1f} / {totals['xg_against']:.1f}")
    columns[3].metric("Avg pass accuracy",
                      f"{totals['avg_pass_accuracy_pct']}%")

    df = pd.DataFrame(stats["matches"])

    st.subheader("Match by match")
    st.dataframe(
        df[["match_date", "opponent", "goals", "goals_against", "xg",
            "xg_against", "shots", "pass_accuracy_pct", "pass_share_pct"]],
        hide_index=True,
        use_container_width=True,
    )

    st.line_chart(df.set_index("match_date")[["xg", "xg_against"]])


def main():
    st.set_page_config(page_title="Football Data Platform", layout="wide")
    st.title("Football Data Platform")

    pages = {
        "Matches": matches_page,
        "Player leaderboard": players_page,
        "Compare players": compare_page,
        "Teams": teams_page,
    }

    page = st.sidebar.radio("Page", list(pages))

    try:
        pages[page]()

    except requests.RequestException as error:
        show_api_error(error)


main()
