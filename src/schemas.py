from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class Move(BaseModel):
    name: str
    power: Optional[int] = None
    accuracy: Optional[int] = None
    type: Optional[str] = None
    category: Optional[str] = None
    effect: Optional[str] = None

class Stats(BaseModel):
    hp: int
    attack: int
    defense: int
    special_attack: int
    special_defense: int
    speed: int

class PokemonResource(BaseModel):
    name: str
    number: Optional[int] = None
    types: List[str]
    abilities: List[str]
    stats: Stats
    generation: Optional[int] = None
    legendary: Optional[bool] = False
    moves: List[Move] = []
    evolution_chain: Optional[Dict[str, Any]] = None
    # additional metadata
    source: Optional[str] = "kaggle+pokeapi"

class BattlePokemonInstance(BaseModel):
    name: str
    level: Optional[int] = 50
    moves: Optional[List[str]] = []  # names of moves to use (if empty, will choose defaults)
    ability: Optional[str] = None
    item: Optional[str] = None
    # can include forced status for testing
    status: Optional[str] = None

class BattleOptions(BaseModel):
    seed: Optional[int] = None
    max_turns: Optional[int] = 200

class BattleRequest(BaseModel):
    pokemon_a: BattlePokemonInstance
    pokemon_b: BattlePokemonInstance
    options: Optional[BattleOptions] = BattleOptions()

class PokemonFinalState(BaseModel):
    name: str
    hp: int
    max_hp: int
    status: Optional[str] = None

class BattleResult(BaseModel):
    battle_log: List[str]
    winner: Optional[str] = None  # "pokemon_a", "pokemon_b", "draw"
    turns: int
    final_states: Dict[str, PokemonFinalState]
