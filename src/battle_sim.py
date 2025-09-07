from typing import Dict, Any, List, Tuple, Optional
from .schemas import BattleRequest, BattleResult, PokemonFinalState
from .data_loader import get_normalized_pokemon
import random
import math


TYPE_CHART = {
    "normal": {"rock": 0.5, "ghost": 0.0, "steel": 0.5},
    "fire": {"grass": 2.0, "ice": 2.0, "bug": 2.0, "steel": 2.0,
             "fire": 0.5, "water": 0.5, "rock": 0.5, "dragon": 0.5},
    "water": {"fire": 2.0, "ground": 2.0, "rock": 2.0,
              "water": 0.5, "grass": 0.5, "dragon": 0.5},
    "electric": {"water": 2.0, "flying": 2.0,
                 "electric": 0.5, "grass": 0.5, "dragon": 0.5,
                 "ground": 0.0},
    "grass": {"water": 2.0, "ground": 2.0, "rock": 2.0,
              "fire": 0.5, "grass": 0.5, "poison": 0.5, "flying": 0.5,
              "bug": 0.5, "dragon": 0.5, "steel": 0.5},
    "ice": {"grass": 2.0, "ground": 2.0, "flying": 2.0, "dragon": 2.0,
            "fire": 0.5, "water": 0.5, "ice": 0.5, "steel": 0.5},
    "fighting": {"normal": 2.0, "ice": 2.0, "rock": 2.0, "dark": 2.0, "steel": 2.0,
                 "poison": 0.5, "flying": 0.5, "psychic": 0.5, "bug": 0.5, "fairy": 0.5,
                 "ghost": 0.0},
    "poison": {"grass": 2.0, "fairy": 2.0,
               "poison": 0.5, "ground": 0.5, "rock": 0.5, "ghost": 0.5,
               "steel": 0.0},
    "ground": {"fire": 2.0, "electric": 2.0, "poison": 2.0, "rock": 2.0, "steel": 2.0,
               "grass": 0.5, "bug": 0.5,
               "flying": 0.0},
    "flying": {"grass": 2.0, "fighting": 2.0, "bug": 2.0,
               "electric": 0.5, "rock": 0.5, "steel": 0.5},
    "psychic": {"fighting": 2.0, "poison": 2.0,
                "psychic": 0.5, "steel": 0.5,
                "dark": 0.0},
    "bug": {"grass": 2.0, "psychic": 2.0, "dark": 2.0,
            "fire": 0.5, "fighting": 0.5, "poison": 0.5, "flying": 0.5,
            "ghost": 0.5, "steel": 0.5, "fairy": 0.5},
    "rock": {"fire": 2.0, "ice": 2.0, "flying": 2.0, "bug": 2.0,
             "fighting": 0.5, "ground": 0.5, "steel": 0.5},
    "ghost": {"psychic": 2.0, "ghost": 2.0,
              "dark": 0.5,
              "normal": 0.0},
    "dragon": {"dragon": 2.0,
               "steel": 0.5,
               "fairy": 0.0},
    "dark": {"psychic": 2.0, "ghost": 2.0,
             "fighting": 0.5, "dark": 0.5, "fairy": 0.5},
    "steel": {"ice": 2.0, "rock": 2.0, "fairy": 2.0,
              "fire": 0.5, "water": 0.5, "electric": 0.5, "steel": 0.5},
    "fairy": {"fighting": 2.0, "dragon": 2.0, "dark": 2.0,
              "fire": 0.5, "poison": 0.5, "steel": 0.5},
}

def type_multiplier(move_type: str, defender_types: List[str]) -> float:
    m = 1.0
    if not move_type:
        return m
    move_type = move_type.lower()
    for dt in defender_types:
        dt_l = dt.lower()
        mult = TYPE_CHART.get(move_type, {}).get(dt_l, 1.0)
        m *= mult
    return m

def choose_default_moves(poke: Dict[str, Any]) -> List[Dict[str,Any]]:
    # If dataset has moves, return first up to 4; otherwise create simple stabs
    moves = poke.get("moves") or []
    if moves:
        return moves[:4]
    t = poke.get("types", ["normal"])[0].lower()
    return [
        {"name": "tackle", "power": 40, "accuracy": 100, "type": "normal", "category": "physical"},
        {"name": f"{t}-blast" , "power": 90, "accuracy": 95, "type": t, "category": "special"}
    ]

def compute_damage(attacker: Dict[str, Any], defender: Dict[str, Any], move: Dict[str, Any], level: int, is_crit: bool, rand_factor: float) -> int:
    power = move.get("power") or 0
    if power == 0:
        return 0
    # choose stats depending on category
    category = (move.get("category") or "").lower()
    if category == "special":
        A = attacker["stats"]["special_attack"]
        D = defender["stats"]["special_defense"]
    else:
        A = attacker["stats"]["attack"]
        D = defender["stats"]["defense"]
    # apply burn halving for physical if attacker has burn (we pass modified stats externally)
    base = (((2 * level) / 5 + 2) * power * (A / max(1, D)) / 50) + 2
    # STAB
    stab = 1.5 if move.get("type") and move.get("type").lower() in [t.lower() for t in attacker.get("types", [])] else 1.0
    # type effectiveness
    te = type_multiplier(move.get("type") or "", attacker.get("_target_types", []))  # We'll set _target_types on defender when calling
    crit = 1.5 if is_crit else 1.0
    modifier = stab * te * crit * rand_factor
    damage = math.floor(base * modifier)
    return max(1, damage)

def simulate_battle(request: BattleRequest) -> BattleResult:
    # Load dataset for both Pokémon
    ra = request.pokemon_a
    rb = request.pokemon_b
    opt = request.options or {}
    seed = opt.seed or random.randint(1, 10**9)
    rnd = random.Random(seed)
    max_turns = opt.max_turns or 200

    p_a_data = get_normalized_pokemon(ra.name)
    p_b_data = get_normalized_pokemon(rb.name)
    if not p_a_data or not p_b_data:
        # build a minimal response
        log = []
        if not p_a_data: log.append(f"Pokémon {ra.name} not found.")
        if not p_b_data: log.append(f"Pokémon {rb.name} not found.")
        final_states = {
            "pokemon_a": PokemonFinalState(name=ra.name, hp=0, max_hp=0, status=None),
            "pokemon_b": PokemonFinalState(name=rb.name, hp=0, max_hp=0, status=None)
        }
        return BattleResult(battle_log=log, winner=None, turns=0, final_states=final_states)

    # create per-battle mutable instances
    def make_instance(data: Dict[str, Any], override: Any):
        max_hp = data["stats"]["hp"]
        inst = {
            "name": data["name"],
            "max_hp": max_hp,
            "hp": max_hp,
            "stats": dict(data["stats"]),
            "types": data.get("types", []),
            "moves": choose_default_moves(data),
            "status": override.status if override and override.status else None,
            "level": override.level if override and override.level else 50,
            "ability": override.ability if override else None,
            "item": override.item if override else None,
            # helper fields
            "_paralyzed": False,
            "_burn": False,
            "_poison": False
        }
        # apply explicit status if provided
        if inst["status"]:
            s = inst["status"].lower()
            if s == "paralysis" or s == "paralyzed": inst["_paralyzed"] = True
            if s == "burn": inst["_burn"] = True
            if s == "poison": inst["_poison"] = True
        return inst

    A = make_instance(p_a_data, ra)
    B = make_instance(p_b_data, rb)

    logs: List[str] = []
    turns = 0

    # set target types helper for damage function
    def set_target_types_for(defender):
        defender["_target_types"] = defender["types"]

    set_target_types_for(A)
    set_target_types_for(B)

    # battle loop
    while A["hp"] > 0 and B["hp"] > 0 and turns < max_turns:
        turns += 1
        logs.append(f"--- Turn {turns} ---")
        # speed with paralysis effect
        a_speed = A["stats"]["speed"] * (0.5 if A["_paralyzed"] else 1.0)
        b_speed = B["stats"]["speed"] * (0.5 if B["_paralyzed"] else 1.0)

        # choose moves: if user specified move names in request prefer those
        def pick_move(instance, request_inst):
            # if request_inst provided moves -> try to match by name
            if request_inst and request_inst.moves:
                for nm in request_inst.moves:
                    # find move in instance moves by name substring match
                    for m in instance["moves"]:
                        if nm.lower() in m["name"].lower():
                            return m
                # fallback to first
            return instance["moves"][rnd.randrange(0, len(instance["moves"]))]

        move_a = pick_move(A, ra)
        move_b = pick_move(B, rb)

        # action order
        order = [(A, move_a, ra, "pokemon_a", B), (B, move_b, rb, "pokemon_b", A)]
        if b_speed > a_speed:
            order = [(B, move_b, rb, "pokemon_b", A), (A, move_a, ra, "pokemon_a", B)]

        # process both actions
        for actor, move, req_inst, actor_label, target in order:
            if actor["hp"] <= 0 or target["hp"] <= 0:
                continue  # fainted mid-turn
            # paralysis check
            if actor["_paralyzed"]:
                p_fail = rnd.random()
                if p_fail < 0.25:
                    logs.append(f"{actor['name']} is paralyzed and couldn't move!")
                    continue
            # accuracy check
            acc = move.get("accuracy") or 100
            if rnd.random() > (acc / 100.0):
                logs.append(f"{actor['name']} used {move['name']} but it missed!")
                continue
            # critical?
            is_crit = rnd.random() < 0.0625  # ~6.25% classic crit
            rand_factor = rnd.uniform(0.85, 1.0)
            # apply burn attack penalty for physical
            saved_attack = actor["stats"]["attack"]
            if actor["_burn"] and (move.get("category") or "physical").lower() != "special":
                actor["stats"]["attack"] = max(1, math.floor(actor["stats"]["attack"] / 2))

            # compute damage (set target types in move context)
            target["_target_types"] = target["types"]
            damage = compute_damage(actor, target, move, actor["level"], is_crit, rand_factor)
            target["hp"] = max(0, target["hp"] - damage)

            # restore attack if modified
            actor["stats"]["attack"] = saved_attack

            te = type_multiplier(move.get("type") or "", target["types"])
            te_msg = ""
            if te == 0.0:
                te_msg = "It has no effect."
            elif te < 1.0:
                te_msg = "It's not very effective."
            elif te > 1.0:
                te_msg = "It's super effective!"

            crit_msg = " A critical hit!" if is_crit else ""
            logs.append(f"{actor['name']} used {move['name']} (power={move.get('power')}) → {damage} dmg.{crit_msg} {te_msg} {target['name']} HP {target['hp']}/{target['max_hp']}")
            # some moves may apply status via effect text - we won't parse; statuses can be applied by request or special chance in future

            if target["hp"] <= 0:
                logs.append(f"{target['name']} fainted!")
                break

        # end of turn effects
        for inst in (A, B):
            if inst["_burn"]:
                chip = max(1, math.floor(inst["max_hp"] / 16))
                inst["hp"] = max(0, inst["hp"] - chip)
                logs.append(f"{inst['name']} is hurt by its burn and loses {chip} HP. {inst['name']} HP {inst['hp']}/{inst['max_hp']}")
                if inst["hp"] <= 0:
                    logs.append(f"{inst['name']} fainted from burn!")
            if inst["_poison"]:
                chip = max(1, math.floor(inst["max_hp"] / 8))
                inst["hp"] = max(0, inst["hp"] - chip)
                logs.append(f"{inst['name']} is hurt by poison and loses {chip} HP. {inst['name']} HP {inst['hp']}/{inst['max_hp']}")
                if inst["hp"] <= 0:
                    logs.append(f"{inst['name']} fainted from poison!")

        # check for end of battle
        if A["hp"] <= 0 or B["hp"] <= 0:
            break

    # decide winner
    if A["hp"] > 0 and B["hp"] <= 0:
        winner = "pokemon_a"
    elif B["hp"] > 0 and A["hp"] <= 0:
        winner = "pokemon_b"
    elif A["hp"] <= 0 and B["hp"] <= 0:
        winner = "draw"
    else:
        # max turns reached
        if A["hp"] > B["hp"]:
            winner = "pokemon_a"
        elif B["hp"] > A["hp"]:
            winner = "pokemon_b"
        else:
            winner = "draw"

    final_states = {
        "pokemon_a": PokemonFinalState(name=A["name"], hp=A["hp"], max_hp=A["max_hp"], status=("burn" if A["_burn"] else ("poison" if A["_poison"] else ("paralysis" if A["_paralyzed"] else None)))),
        "pokemon_b": PokemonFinalState(name=B["name"], hp=B["hp"], max_hp=B["max_hp"], status=("burn" if B["_burn"] else ("poison" if B["_poison"] else ("paralysis" if B["_paralyzed"] else None))))
    }

    return BattleResult(battle_log=logs, winner=winner, turns=turns, final_states=final_states)
