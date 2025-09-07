import pandas as pd
from pathlib import Path
from typing import Dict, Any, List, Optional
from .pokeapi_client import get_pokemon_data_from_api, get_species_from_api, get_move_from_api, get_evolution_chain_by_url
from .utils import ensure_dirs, write_json_file
import json
import re

ensure_dirs()

DATA_RAW = Path(__file__).resolve().parents[1] / "data" / "raw" / "All_Pokemon.csv"
NORMALIZED_DIR = Path(__file__).resolve().parents[1] / "data" / "normalized"
NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)

def normalize_name(n: str) -> str:
    return re.sub(r"[^a-z0-9\-]", "", n.lower().replace(" ", "-"))

def load_kaggle_dataframe() -> pd.DataFrame:
    if not DATA_RAW.exists():
        raise FileNotFoundError(f"Place the Kaggle CSV at {DATA_RAW}")
    df = pd.read_csv(DATA_RAW)
    # drop rows without Name
    df = df[df["Name"].notna()]
    return df

def parse_abilities(cell: Any) -> List[str]:
    if pd.isna(cell):
        return []
    if isinstance(cell, str):
        # split on comma, strip
        return [a.strip() for a in cell.split(",") if a.strip()]
    return []

def build_basic_from_row(row: pd.Series) -> Dict[str, Any]:
    types = []
    t1 = row.get("Type 1")
    t2 = row.get("Type 2")
    if pd.notna(t1): types.append(str(t1).strip())
    if pd.notna(t2) and str(t2).strip(): types.append(str(t2).strip())
    abilities = parse_abilities(row.get("Abilities", ""))
    stats = {
        "hp": int(row.get("HP", 1)),
        "attack": int(row.get("Att", 1)),
        "defense": int(row.get("Def", 1)),
        "special_attack": int(row.get("Spa", 1)),
        "special_defense": int(row.get("Spd", 1)),
        "speed": int(row.get("Spe", 1)),
    }
    obj = {
        "name": row["Name"],
        "number": int(row.get("Number", 0)) if not pd.isna(row.get("Number")) else None,
        "types": types or ["normal"],
        "abilities": abilities,
        "stats": stats,
        "generation": int(row.get("Generation", 0)) if not pd.isna(row.get("Generation")) else None,
        "legendary": bool(row.get("Legendary")) if "Legendary" in row else False
    }
    return obj

def enrich_with_pokeapi(name: str, basic: Dict[str, Any]) -> Dict[str, Any]:
    # attempt to fetch moves & evolution from pokeapi
    api_poke = get_pokemon_data_from_api(name)
    moves_list = []
    evolution_chain = None

    if api_poke:
        # moves: list of dicts with move name and url - we'll fetch move details lazily/truncate
        for m in api_poke.get("moves", []):
            move_entry = m.get("move", {})
            moves_list.append({"name": move_entry.get("name"), "url": move_entry.get("url")})
    else:
        moves_list = []

    # species -> evolution chain
    species = get_species_from_api(name)
    if species:
        evo = species.get("evolution_chain")
        if evo and evo.get("url"):
            chain = get_evolution_chain_by_url(evo.get("url"))
            evolution_chain = chain

    # try to fetch detailed move info for top N moves (limit to e.g., 8 to save time)
    detailed_moves = []
    limit = 8
    for i, m in enumerate(moves_list[:limit]):
        move_name = m.get("name")
        move_data = get_move_from_api(move_name) if move_name else None
        if move_data:
            detailed_moves.append({
                "name": move_data.get("name"),
                "power": move_data.get("power"),
                "accuracy": move_data.get("accuracy"),
                "type": move_data.get("type", {}).get("name") if move_data.get("type") else None,
                "category": move_data.get("damage_class", {}).get("name") if move_data.get("damage_class") else None,
                "effect": (move_data.get("effect_entries") or [{}])[0].get("short_effect") if move_data.get("effect_entries") else None
            })
        else:
            # fallback minimal move object
            detailed_moves.append({
                "name": move_name or "tackle",
                "power": 40,
                "accuracy": 100,
                "type": basic["types"][0].lower() if basic.get("types") else "normal",
                "category": "physical",
                "effect": None
            })

    out = dict(basic)
    out["moves"] = detailed_moves
    out["evolution_chain"] = evolution_chain
    return out

def normalize_all_and_write():
    df = load_kaggle_dataframe()
    for _, row in df.iterrows():
        basic = build_basic_from_row(row)
        name = basic["name"]
        try:
            enriched = enrich_with_pokeapi(name, basic)
        except Exception:
            enriched = basic
        safe = normalize_name(name)
        write_json_file(NORMALIZED_DIR / f"{safe}.json", enriched)

def get_normalized_pokemon(name: str) -> Optional[Dict[str, Any]]:
    safe = normalize_name(name)
    p = NORMALIZED_DIR / f"{safe}.json"
    if p.exists():
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    # try building on the fly
    df = load_kaggle_dataframe()
    row = df[df["Name"].str.lower() == name.lower()]
    if row.empty:
        # try partial match
        row = df[df["Name"].str.lower().str.contains(name.lower())]
        if row.empty:
            return None
    row0 = row.iloc[0]
    basic = build_basic_from_row(row0)
    try:
        enriched = enrich_with_pokeapi(basic["name"], basic)
    except Exception:
        enriched = basic
    write_json_file(NORMALIZED_DIR / f"{normalize_name(basic['name'])}.json", enriched)
    return enriched
