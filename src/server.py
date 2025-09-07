# src/server.py
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from .data_loader import get_normalized_pokemon, normalize_all_and_write
from .schemas import PokemonResource, BattleRequest, BattleResult
from .battle_sim import simulate_battle
from typing import Dict, Any
from pathlib import Path
import json

app = FastAPI(title="Pokemon MCP Server (MCP-like)")

# Minimal discovery endpoint following MCP idea
@app.get("/.well-known/mcp")
def discovery():
    # This is a lightweight discovery descriptor: list resources and tools and sample schemas
    resources = {
        "pokemon_data": {
            "description": "Comprehensive pokemon data resource",
            "endpoint": "/mcp/resources/pokemon_data/{name}",
            "schema": "schemas.PokemonResource (see /docs)"
        }
    }
    tools = {
        "pokemon_battle_simulator": {
            "description": "Simulate a battle between two pokemon",
            "endpoint": "/mcp/tools/battle/simulate",
            "input": "schemas.BattleRequest",
            "output": "schemas.BattleResult"
        }
    }
    return {"resources": resources, "tools": tools}

@app.get("/mcp/resources/pokemon_data/{name}", response_model=PokemonResource)
def pokemon_resource(name: str):
    p = get_normalized_pokemon(name)
    if not p:
        raise HTTPException(status_code=404, detail=f"Pokemon {name} not found")
    # massage into schema-friendly shape
    # ensure stats object has expected keys
    stats = p.get("stats", {})
    return PokemonResource(
        name=p.get("name"),
        number=p.get("number"),
        types=p.get("types", []),
        abilities=p.get("abilities", []),
        stats={
            "hp": int(stats.get("hp", 1)),
            "attack": int(stats.get("attack", 1)),
            "defense": int(stats.get("defense", 1)),
            "special_attack": int(stats.get("special_attack", stats.get("spa", 1))),
            "special_defense": int(stats.get("special_defense", stats.get("spd", 1))),
            "speed": int(stats.get("speed", stats.get("spe", 1))),
        },
        generation=p.get("generation"),
        legendary=p.get("legendary", False),
        moves=p.get("moves", []),
        evolution_chain=p.get("evolution_chain", None)
    )

@app.post("/mcp/tools/battle/simulate", response_model=BattleResult)
def battle_sim_tool(payload: BattleRequest):
    # run simulation
    result = simulate_battle(payload)
    return result

# util route to normalize whole dataset (heavy)
@app.post("/admin/normalize_all")
def admin_normalize_all():
    try:
        normalize_all_and_write()
        return {"status": "ok"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.server:app", host="0.0.0.0", port=8000, reload=True)
