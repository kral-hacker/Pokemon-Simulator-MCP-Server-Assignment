# Pokémon MCP Server

## 📌 Overview
This project implements a **Model Context Protocol (MCP) server** that gives AI models structured access to Pokémon knowledge and battle simulation.  

It was built as part of the **Pokémon Battle Simulation - MCP Server Technical Assessment** and exposes two main capabilities:

- **Pokémon Data Resource** – A comprehensive Pokémon knowledge base (types, stats, abilities, moves, evolutions).  
- **Battle Simulation Tool** – A battle simulator implementing Pokémon mechanics such as type effectiveness, damage calculation, turn order, and status effects.  

**Documentation for both features (Data Resource and Battle Simulation)** is provided inside the `documentation/` folder.

---

## 📂 Project Structure
```bash
src/
│── server.py # MCP server entrypoint (FastAPI)
│── data_loader.py # Hybrid data loader (Kaggle + PokeAPI)
│── battle_sim.py # Core Pokémon battle simulation engine
│── schemas.py # Pydantic models for requests & responses
│── normalized_data/ # JSON files of Pokémon after normalization
documentation/ # Detailed docs for Data Resource & Battle Simulator"""
```

---

## 🛠 Design Decisions

### 🔹 Hybrid Dataset (Kaggle + PokeAPI)
- Kaggle dataset provides fast bulk access to Pokémon stats (HP, Attack, Defense, etc.).  
- PokeAPI provides dynamic data (abilities, moves, evolution chains).  
- **Goal:** Reduce API load while ensuring complete Pokémon information.  

### 🔹 Normalization Script
The `normalize_all_and_write()` script merges Kaggle + PokeAPI data.  
Each Pokémon is stored as a JSON file with unified fields:
- `stats` (HP, Attack, Defense, etc.)  
- `types`  
- `abilities`  
- `moves`  
- `evolution_chain`  

This ensures **fast and consistent queries**.

### 🔹 MCP Integration
- **Discovery Endpoint (`/.well-known/mcp`)** – Advertises available resources and tools.  
- **Pokémon Resource (`/mcp/resources/pokemon_data/{name}`)** – Exposes normalized Pokémon JSON.  
- **Battle Simulation Tool (`/mcp/tools/battle/simulate`)** – Runs a turn-based battle simulation.  

---

## 🚀 Running the Server

1. Install dependencies:
```bash
pip install -r requirements.txt
```


2. Start server:
```bash
uvicorn src.server:app --reload --host 0.0.0.0 --port 8000
```

3. Access endpoints:
- Swagger UI → [http://localhost:8000/docs](http://localhost:8000/docs)  
- ReDoc → [http://localhost:8000/redoc](http://localhost:8000/redoc)  
- OpenAPI Spec → [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)  
- MCP Discovery → [http://localhost:8000/.well-known/mcp](http://localhost:8000/.well-known/mcp)  

---

## 📖 API Documentation

### 🔹 Discovery Endpoint
`GET /.well-known/mcp`  

Returns available resources and tools.  

**Example Response:**
```bash
{
"resources": {
"pokemon_data": {
"description": "Comprehensive pokemon data resource",
"endpoint": "/mcp/resources/pokemon_data/{name}"
}
},
"tools": {
"pokemon_battle_simulator": {
"description": "Simulate a battle between two pokemon",
"endpoint": "/mcp/tools/battle/simulate"
}
}
}
```

---

### 🔹 Pokémon Data Resource
`GET /mcp/resources/pokemon_data/{name}`  

Fetches normalized Pokémon data.  

**Example:**
```bash
curl http://localhost:8000/mcp/resources/pokemon_data/pikachu
```


**Response:**
```bash
{
"name": "pikachu",
"number": 25,
"types": ["Electric"],
"abilities": ["Static", "Lightning Rod"],
"stats": {
"hp": 35,
"attack": 55,
"defense": 40,
"special_attack": 50,
"special_defense": 50,
"speed": 90
},
"generation": 1,
"legendary": false,
"moves": [...],
"evolution_chain": "pichu → pikachu → raichu"
}
```


---

### 🔹 Battle Simulation Tool
`POST /mcp/tools/battle/simulate`  

Runs a battle between two Pokémon.  

**Example Request:**
```bashcurl -X POST http://localhost:8000/mcp/tools/battle/simulate
-H "Content-Type: application/json"
-d '{
"pokemon_a": {"name": "pikachu"},
"pokemon_b": {"name": "charmander"},
"options": {"max_turns": 50, "seed": 42}
}'
```


**Response (excerpt):**
```bash
{
"battle_log": [
"--- Turn 1 ---",
"Pikachu used Thunderbolt → 45 dmg. It's super effective! Charmander HP 10/39",
"Charmander used Ember → 12 dmg. Pikachu HP 23/35",
"Charmander fainted!"
],
"winner": "pokemon_a",
"turns": 1,
"final_states": {
"pokemon_a": {"name": "Pikachu", "hp": 23, "max_hp": 35, "status": null},
"pokemon_b": {"name": "Charmander", "hp": 0, "max_hp": 39, "status": null}
}
}
```


---

## ⚡ Features Implemented
- ✅ **Pokémon Data Resource**  
  - Base stats  
  - Types  
  - Abilities  
  - Moves  
  - Evolutions  

- ✅ **Battle Simulator**  
  - Type effectiveness  
  - Damage calculation  
  - Turn order (with paralysis speed effect)  
  - Status effects: Burn, Poison, Paralysis  
  - Random critical hits  
  - End-of-turn status damage  

---

## 📊 Examples of LLM Queries
- **Query a Pokémon’s stats**  
  *"Give me the stats, abilities, and evolution chain of Pikachu."*  
  → LLM calls `/mcp/resources/pokemon_data/pikachu`.

- **Simulate a battle**  
  *"Who would win in a battle between Bulbasaur and Squirtle?"*  
  → LLM calls `/mcp/tools/battle/simulate` with:
```bash
{"pokemon_a": {"name": "bulbasaur"}, "pokemon_b": {"name": "squirtle"}}
```


---

## 📌 Conclusion
The **Pokémon MCP Server** bridges Pokémon data and battle mechanics with AI models through a standardized interface.  

It provides both **static data (resource)** and **dynamic interactions (battle simulation)**, making it a robust playground for **Pokémon + LLM integrations**.  

For detailed API and simulation documentation, check the `documentation/` folder.
