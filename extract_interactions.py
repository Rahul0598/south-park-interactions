import os
import json
import re
from collections import defaultdict
from itertools import combinations
from sentence_transformers import SentenceTransformer, util

def load_character_aliases(char_file):
    with open(char_file, 'r') as f:
        char_data = json.load(f)

    name_map = defaultdict(set)
    for entry in char_data.get("main_characters", []):
        canonical = entry["name"]
        name_map[canonical].add(canonical)
        for fam in entry.get("family", []):
            fam_name = re.sub(r"\(.*?\)", "", fam).strip()
            name_map[canonical].add(fam_name)
        parts = canonical.split()
        if len(parts) > 1:
            name_map[canonical].add(parts[-1])
            name_map[canonical].add("Mr. " + parts[-1])
            name_map[canonical].add("Dr. " + parts[-1])
            name_map[canonical].add(parts[0])

    manual_aliases = {
        "Kim": "Tuong Lu Kim",
        "Mr. Kim": "Tuong Lu Kim",
        "Mr. Lu Kim": "Tuong Lu Kim",
        "Lu Kim": "Tuong Lu Kim",
        "Cartman": "Eric Cartman",
        "Eric": "Eric Cartman",
        "Chef": "Jerome \"Chef\" McElroy"
    }
    for alias, canonical in manual_aliases.items():
        name_map[canonical].add(alias)

    alias_to_canonical = {}
    for canon, aliases in name_map.items():
        for alias in aliases:
            alias_to_canonical[alias.lower()] = canon

    return alias_to_canonical

def normalize_name(name, alias_map):
    name = name.strip().lower()
    name = re.sub(r'^(mr\.|mrs\.|ms\.|dr\.) ', '', name)
    normalized = alias_map.get(name, alias_map.get(name.split()[0] if name.split() else name, name.title()))
    return normalized

def extract_interactions(script_json, model, alias_map, filename, window_size=3, sim_threshold=0.4):
    episode_title = None
    dialogues = []

    # Extract season and episode from filename (e.g., S10E05.json)
    season, episode_num = None, None
    match = re.match(r'S(\d+)E(\d+)\.json', filename)
    if match:
        season = int(match.group(1))
        episode_num = int(match.group(2))

    for entry in script_json:
        if entry['type'] == 'scene' and not episode_title:
            episode_title = entry['description']
        elif entry['type'] == 'dialogue':
            character = normalize_name(entry['character'], alias_map)
            line = entry['line'].strip()
            if character and line:
                dialogues.append((character, line))

    sentences = [line for _, line in dialogues]
    embeddings = model.encode(sentences, convert_to_tensor=True) if sentences else None

    interactions = set()

    for i in range(len(dialogues)):
        char_i, line_i = dialogues[i]
        if i < len(dialogues) - 1:
            char_j, _ = dialogues[i + 1]
            if char_i != char_j:
                pair = tuple(sorted([char_i, char_j]))
                interactions.add(pair)

        if embeddings is not None:
            for j in range(i + 1, min(i + 1 + window_size, len(dialogues))):
                char_j, _ = dialogues[j]
                if char_i == char_j:
                    continue
                sim = util.cos_sim(embeddings[i], embeddings[j]).item()
                if sim >= sim_threshold:
                    pair = tuple(sorted([char_i, char_j]))
                    interactions.add(pair)

    return {
        "episode": episode_title,
        "season": season,
        "episode_num": episode_num,
        "interactions": list(interactions)
    }

def process_all_scripts(script_folder, char_file):
    alias_map = load_character_aliases(char_file)
    model = SentenceTransformer("all-MiniLM-L6-v2")
    dataset = []
    for filename in os.listdir(script_folder):
        if filename.endswith(".json"):
            with open(os.path.join(script_folder, filename), 'r', encoding='utf-8') as f:
                script_data = json.load(f)
                episode_data = extract_interactions(script_data, model, alias_map, filename)
                dataset.append(episode_data)
    return dataset

def save_dataset(dataset, out_path):
    with open(out_path, 'w') as f:
        json.dump(dataset, f, indent=2)

def search_episodes_with_characters(dataset, alias_map, character_list):
    normalized = [normalize_name(name, alias_map) for name in character_list]
    matching_episodes = []
    for episode_data in dataset:
        interactions = [tuple(sorted(i)) for i in episode_data["interactions"]]
        for combo in combinations(normalized, 2):
            if tuple(sorted(combo)) in interactions:
                episode_info = {
                    "episode": episode_data["episode"],
                    "season": episode_data["season"],
                    "episode_num": episode_data["episode_num"]
                }
                matching_episodes.append(episode_info)
                break
    return list({f"{ep['episode']} (S{ep['season']:02d}E{ep['episode_num']:02d})" for ep in matching_episodes})

if __name__ == "__main__":
    SCRIPT_FOLDER = "./south_park_scripts"
    CHAR_FILE = "./characters.json"
    OUT_FILE = "./interactions_dataset.json"
    print("Processing scripts and extracting interactions...")
    dataset = process_all_scripts(SCRIPT_FOLDER, CHAR_FILE)
    save_dataset(dataset, OUT_FILE)
    with open(OUT_FILE, "r") as f:
        data = json.load(f)
    alias_map = load_character_aliases(CHAR_FILE)
    result = search_episodes_with_characters(data, alias_map, ["Cartman", "Kim"])
    print("\nEpisodes where Cartman and Kim interact:\n", result)