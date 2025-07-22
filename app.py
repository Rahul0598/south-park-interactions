import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
import networkx as nx
from itertools import combinations
from extract_interactions import load_character_aliases, normalize_name

# Set Streamlit page configuration
st.set_page_config(page_title="South Park Interaction Explorer", layout="centered")

# Custom CSS for modern, minimalist styling
st.markdown("""
    <style>
    .stApp {
        background-color: #f8f9fa;
        font-family: 'Helvetica Neue', Arial, sans-serif;
    }
    .title {
        text-align: center;
        color: #2c3e50;
        font-size: 2.5em;
        font-weight: 700;
        margin-bottom: 0.5em;
    }
    .subtitle {
        text-align: center;
        color: #34495e;
        font-size: 1.2em;
        font-weight: 400;
        margin-bottom: 2em;
    }
    .stTextInput > div > div > input {
        border: 1px solid #dcdcdc;
        border-radius: 8px;
        padding: 10px;
        font-size: 1em;
        background-color: #ffffff;
    }
    .stButton > button {
        background-color: #3498db;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        font-size: 1em;
        font-weight: 500;
        border: none;
        transition: background-color 0.3s;
    }
    .stButton > button:hover {
        background-color: #2980b9;
    }
    .episode-list {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    .episode-list ul {
        list-style-type: none;
        padding: 0;
    }
    .episode-list li {
        padding: 8px 0;
        color: #2c3e50;
        font-size: 1em;
    }
    .viz-container {
        background-color: #ffffff;
        border-radius: 8px;
        padding: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    with open("interactions_dataset.json", "r") as f:
        dataset = json.load(f)
    alias_map = load_character_aliases("characters.json")
    return dataset, alias_map

def find_shared_interaction_episodes(dataset, normalized_characters):
    matching_episodes = []
    all_interactions = []
    episode_details = []

    for episode_data in dataset:
        interactions = [tuple(sorted(i)) for i in episode_data["interactions"]]
        required_pairs = list(combinations(normalized_characters, 2))
        if all(tuple(sorted(pair)) in interactions for pair in required_pairs):
            episode_name = episode_data["episode"]
            season = episode_data.get("season")
            episode_num = episode_data.get("episode_num")
            matching_episodes.append(f"{episode_name} (S{season:02d}E{episode_num:02d})")
            episode_details.append({"episode": episode_name, "season": season, "episode_num": episode_num})
            all_interactions.extend([
                (ep[0], ep[1]) for ep in interactions
                if ep[0] in normalized_characters and ep[1] in normalized_characters
            ])

    return matching_episodes, all_interactions, episode_details

def create_network_graph(interactions, characters):
    G = nx.Graph()
    G.add_nodes_from(characters)
    for a, b in interactions:
        G.add_edge(a, b)
    
    pos = nx.spring_layout(G)
    edge_x = []
    edge_y = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])

    edge_trace = go.Scatter(
        x=edge_x, y=edge_y,
        line=dict(width=1, color="#888"),
        hoverinfo="none",
        mode="lines"
    )

    node_x = [pos[node][0] for node in G.nodes()]
    node_y = [pos[node][1] for node in G.nodes()]
    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode="markers+text",
        text=list(G.nodes()),
        textposition="top center",
        marker=dict(size=20, color="#3498db", line=dict(width=2, color="#2c3e50")),
        hoverinfo="text"
    )

    fig = go.Figure(data=[edge_trace, node_trace],
                    layout=go.Layout(
                        title="Character Interaction Network",
                        title_x=0.5,
                        showlegend=False,
                        hovermode="closest",
                        margin=dict(b=20, l=5, r=5, t=40),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        plot_bgcolor="rgba(0,0,0,0)",
                        paper_bgcolor="rgba(0,0,0,0)"
                    ))
    return fig

def create_episode_timeline(episode_details):
    if not episode_details or not any(d["season"] is not None and d["episode_num"] is not None for d in episode_details):
        return None
    df = pd.DataFrame(episode_details)
    df = df.dropna(subset=["season", "episode_num"])
    df["episode_label"] = df["episode"] + " (S" + df["season"].astype(int).astype(str).str.zfill(2) + "E" + df["episode_num"].astype(int).astype(str).str.zfill(2) + ")"

    fig = go.Figure(data=[
        go.Scatter(
            x=df["season"],
            y=df["episode_num"],
            mode="markers+text",
            text=df["episode_label"],
            textposition="top center",
            marker=dict(size=12, color="#3498db"),
            hovertemplate="%{text}<br>Season: %{x}<br>Episode: %{y}"
        )
    ])

    fig.update_layout(
        title="Episode Interaction Timeline",
        title_x=0.5,
        xaxis_title="Season",
        yaxis_title="Episode Number",
        xaxis=dict(tickmode="linear", tick0=1, dtick=1),
        yaxis=dict(tickmode="linear", tick0=1, dtick=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(b=20, l=50, r=50, t=40)
    )
    return fig

def main():
    st.markdown('<div class="title">South Park Interaction Explorer</div>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">Discover episodes where your favorite characters interact</div>', unsafe_allow_html=True)

    with st.form(key="character_form"):
        input_chars = st.text_input(
            "Enter character names (e.g., Cartman, Butters, Kim):",
            placeholder="Type names separated by commas",
            help="Enter at least two character names to find episodes where they interact."
        )
        submit_button = st.form_submit_button("Find Episodes")

    if not submit_button:
        return

    char_list = [c.strip() for c in input_chars.split(",") if c.strip()]
    if len(char_list) < 2:
        st.warning("Please enter at least two character names.")
        return

    dataset, alias_map = load_data()
    normalized_chars = [normalize_name(name, alias_map) for name in char_list]

    st.markdown(f"**Looking for interactions between**: {', '.join(normalized_chars)}")

    episodes, interactions, episode_details = find_shared_interaction_episodes(dataset, normalized_chars)

    if not episodes:
        st.error("No episodes found where all selected characters interact directly.")
        return

    st.markdown('<div class="episode-list"><h3>Episodes Found</h3><ul>' + 
                ''.join(f'<li>{ep}</li>' for ep in episodes) + 
                '</ul></div>', unsafe_allow_html=True)

    st.markdown('<div class="viz-container"><h3>Interaction Network</h3></div>', unsafe_allow_html=True)
    network_fig = create_network_graph(interactions, normalized_chars)
    st.plotly_chart(network_fig, use_container_width=True)

    st.markdown('<div class="viz-container"><h3>Episode Timeline</h3></div>', unsafe_allow_html=True)
    timeline_fig = create_episode_timeline(episode_details)
    if timeline_fig:
        st.plotly_chart(timeline_fig, use_container_width=True)
    else:
        st.info("Timeline not available due to missing season/episode data.")

if __name__ == "__main__":
    main()