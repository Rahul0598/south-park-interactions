# South Park Interaction Explorer

A simple tool for *South Park* fans to find episodes where their favorite characters, like Cartman or Mr. Kim, interact.

## How It Works

- **Input**: Enter the names of your favorite characters (e.g., "Cartman, Kim") in the web app.
- **Output**: Get a list of episodes where those characters interact, plus cool visualizations like a network graph showing who talks to whom and a timeline of episodes across seasons.
- **Data**: Uses *South Park* script files from [South Park Fandom](https://southpark.fandom.com/wiki/Portal:Scripts) to extract character interactions.

## Setup

1. **Install Requirements**:
   ```bash
   pip install streamlit pandas plotly networkx sentence-transformers
   ```

2. **Run the App**:
   ```bash
   streamlit run app.py
   ```
   Open the link in your browser, enter character names, and find episodes!

## Next Steps

- Add a feature to search for episodes based on specific scenarios (e.g., "Cartman scams someone") to make rewatching even more fun.

## Why I Built This

I’m a huge *South Park* fan and wanted an easy way to rewatch episodes with my favorite characters’ best moments. This tool makes it simple to find those episodes, and I’m excited to keep improving it!