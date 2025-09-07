import httpx
from typing import Optional, Dict, Any
from .utils import cache_path_for, load_json_file, write_json_file, ensure_dirs
import time

BASE = "https://pokeapi.co/api/v2"

ensure_dirs()

_client = httpx.Client(timeout=10.0)

def fetch_and_cache(endpoint: str) -> Optional[Dict[str, Any]]:
    """
    endpoint e.g. "pokemon/pikachu" or "move/85"
    caches under data/cache/pokeapi/{endpoint}.json
    """
    cache_p = cache_path_for(endpoint)
    cached = load_json_file(cache_p)
    if cached is not None:
        return cached

    url = f"{BASE}/{endpoint.strip('/')}"
    try:
        r = _client.get(url)
        if r.status_code == 200:
            data = r.json()
            write_json_file(cache_p, data)
            # be polite to api
            time.sleep(0.05)
            return data
        else:
            return None
    except Exception:
        return None

def get_pokemon_data_from_api(name: str) -> Optional[Dict[str, Any]]:
    return fetch_and_cache(f"pokemon/{name.lower()}")

def get_move_from_api(move_name_or_id: str) -> Optional[Dict[str, Any]]:
    return fetch_and_cache(f"move/{move_name_or_id}")

def get_species_from_api(name: str) -> Optional[Dict[str, Any]]:
    return fetch_and_cache(f"pokemon-species/{name.lower()}")

def get_evolution_chain_by_url(url: str) -> Optional[Dict[str, Any]]:
    # url like https://pokeapi.co/api/v2/evolution-chain/1/
    endpoint = url.replace(BASE + "/", "")
    return fetch_and_cache(endpoint)
