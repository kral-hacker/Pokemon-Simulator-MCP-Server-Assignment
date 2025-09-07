import requests

BASE_URL = "http://localhost:8000"

def test_discovery():
    print("🔍 Checking MCP Discovery Endpoint...")
    r = requests.get(f"{BASE_URL}/.well-known/mcp")
    print("Status:", r.status_code)
    print("Response:", r.json())

def test_pokemon_data():
    print("\n⚡ Checking Pokemon Data (Pikachu)...")
    r = requests.get(f"{BASE_URL}/mcp/resources/pokemon_data/Pikachu")
    print("Status:", r.status_code)
    print("Response:", r.json())

def test_battle_sim():
    print("\n⚔️ Checking Battle Simulation...")
    payload = {
        "pokemon_a": {
            "name": "Pikachu",
            "level": 50,
            "moves": ["Thunderbolt"],
            "ability": "Static",
            "item": "Light Ball",
            "status": ""
        },
        "pokemon_b": {
            "name": "Charizard",
            "level": 50,
            "moves": ["Flamethrower"],
            "ability": "Blaze",
            "item": "Leftovers",
            "status": ""
        },
        "options": {"max_turns": 10}
    }
    r = requests.post(f"{BASE_URL}/mcp/tools/battle/simulate", json=payload)
    print("Status:", r.status_code)
    print("Response:", r.json())

if __name__ == "__main__":
    test_discovery()
    test_pokemon_data()
    test_battle_sim()
