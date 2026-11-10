# The Village Treasure

A choice-driven, single-player adventure made with Python and Pygame. Explore Willowmere, collect and use items, speak with its residents, and uncover Alden Willow's treasure.

## Run

Install the listed dependency if needed, then run:

```powershell
python -m pip install -r requirements.txt
python main.py
```

## Controls

- Enter a player name, then press **Enter** or click **Begin Journey**.
- Click an available action, or use **Up/Down** and **Enter** to choose one.
- Travel with **W = North**, **S = South**, **A = West**, and **D = East**, or click a lit travel key.
- Click an inventory slot or press **1, 2, 3, or 4** to select and inspect an item; press **E** to use it where appropriate.
- Press **Tab** to cycle through inventory items. Click or press **Enter/Space** to continue dialogue.

## Optional assets

Assets are loaded from `content/assets/` when present. Missing images, fonts, music, and sound effects use built-in placeholders or remain silent. Expected sprite paths and location backgrounds are defined by the JSON files in `content/data/` and `content/maps/world_map.json`.