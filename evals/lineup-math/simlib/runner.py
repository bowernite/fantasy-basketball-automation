"""Run sim jobs from JSON config. See `.claude/skills/sims/config.md`."""
import json
import os
import re
from datetime import date

import sim
from fetch_data import SEASON_TAG
from simlib import roster
from simlib.data import HERE
from simlib.reports import OURS_ONLY, REPORTS

EVAL_BASE = {
    "us": os.path.join(HERE, "..", "teams", "my-team", "My Team.md"),
    "161024": os.path.join(HERE, "..", "teams", "josh", "Josh's Team.md"),
}

_BASE_CACHE = {}

KINDS = ("reports", "trade-screen", "player-effects", "title-column")


def resolve_roster(ref):
    if ref is None:
        return None
    if isinstance(ref, int):
        return "roster-%d-%s.json" % (ref, SEASON_TAG)
    s = str(ref).strip()
    if s.isdigit():
        return "roster-%s-%s.json" % (s, SEASON_TAG)
    if not s.endswith(".json"):
        s += ".json"
    return s


def parse_config(raw):
    if isinstance(raw, str):
        with open(raw) as f:
            raw = json.load(f)
    if "sections" in raw:
        return raw["sections"]
    if "kind" in raw:
        return [raw]
    raise ValueError("config needs 'kind' or 'sections'")


def validate_section(sec):
    kind = sec.get("kind")
    if kind not in KINDS:
        raise ValueError("unknown kind: %r (expected one of %s)"
                         % (kind, ", ".join(KINDS)))
    if kind == "reports":
        if "names" not in sec:
            raise ValueError("reports section needs 'names'")
        unknown = [n for n in sec["names"] if n not in REPORTS]
        if unknown:
            raise ValueError("unknown report: %s" % ", ".join(unknown))
        path = resolve_roster(sec.get("roster"))
        if path:
            bad = [n for n in sec["names"] if n in OURS_ONLY]
            if bad:
                raise ValueError("reports %s refuse counterparty roster"
                                 % ", ".join(bad))
    elif kind == "trade-screen":
        for key in ("their_roster", "deals"):
            if key not in sec:
                raise ValueError("trade-screen section needs %r" % key)
        for deal in sec["deals"]:
            for key in ("out_us", "in_from_them", "out_them", "in_from_us"):
                if key not in deal:
                    raise ValueError("deal %r needs %r"
                                     % (deal.get("label", deal), key))
    elif kind == "player-effects":
        for key in ("their_roster", "groups"):
            if key not in sec:
                raise ValueError("player-effects section needs %r" % key)
        for group in sec["groups"]:
            for key in ("label", "source", "names"):
                if key not in group:
                    raise ValueError("player-effects group needs %r" % key)
            if group["source"] not in ("us", "their"):
                raise ValueError("group source must be 'us' or 'their'")
    elif kind == "title-column":
        include = sec.get("include") or ["ours", "their_incoming"]
        if "their_incoming" in include and not sec.get("their_roster"):
            raise ValueError("title-column with their_incoming needs their_roster")


def bodies(names, roster_rows):
    by = {p["n"]: p for p in roster_rows}
    missing = [n for n in names if n not in by]
    if missing:
        raise KeyError("missing on roster: %s" % ", ".join(missing))
    return [by[n] for n in names]


TITLE_NOTE = "both rosters change in the 12-team field"


def price_deal(deal, their, our_proj, their_proj, before=None):
    after_ours = sim.basis_after_trade(
        None, deal["out_us"], bodies(deal["in_from_them"], their_proj))
    after_theirs = sim.basis_after_trade(
        their, deal["out_them"], bodies(deal["in_from_us"], our_proj))
    after_us, before_us, after_them, before_them = sim.deal_odds(
        after_ours, after_theirs, their, before=before)
    return (after_us.wins - before_us.wins, after_us.title - before_us.title,
            after_them.wins - before_them.wins,
            after_them.title - before_them.title)


def _load_base(path):
    if path in _BASE_CACHE:
        return _BASE_CACHE[path]
    out = {}
    with open(path) as f:
        for line in f:
            if not line.startswith("|") or line.startswith("| ---"):
                continue
            parts = [p.strip() for p in line.split("|")]
            if len(parts) < 6:
                continue
            name = parts[1]
            if name in ("Player", "---"):
                continue
            m = re.search(r"\*\*([\d,]+)\*\*", parts[5])
            if m:
                out[name] = int(m.group(1).replace(",", ""))
    _BASE_CACHE[path] = out
    return out


def _player_base(names, path):
    table = _load_base(path)
    total, missing = 0, []
    for n in names:
        if n in ("Keon Ellis", "Gary Payton", "Karlo Matković"):
            if n not in table:
                table = _load_base(path)
        if n in table:
            total += table[n]
        else:
            missing.append(n)
    if missing:
        raise KeyError("BASE missing for: %s" % ", ".join(missing))
    return total


def deal_delta_base(deal, their_roster):
    key = str(their_roster) if isinstance(their_roster, int) else "161024"
    their_path = EVAL_BASE.get(key, EVAL_BASE["161024"])
    try:
        return (_player_base(deal["in_from_them"], their_path)
                - _player_base(deal["out_us"], EVAL_BASE["us"]))
    except KeyError:
        return None


def _trade_screen_results(sec):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    our_proj = sim.our_roster()
    their_proj = sim.our_roster(their)
    before = sim.full_season()
    rows = []
    for deal in sec["deals"]:
        name = deal.get("label") or "deal"
        row = {"label": name}
        try:
            dw_us, dt_us, dw_them, dt_them = price_deal(
                deal, their, our_proj, their_proj, before)
            row["results"] = {
                "delta_base_us": deal_delta_base(deal, sec["their_roster"]),
                "dw_us": round(dw_us, 2),
                "dp_title_us": round(dt_us * 100, 1),
                "dw_them": round(dw_them, 2),
                "dp_title_them": round(dt_them * 100, 1),
                "dp_title_note": TITLE_NOTE,
            }
        except (KeyError, ValueError) as e:
            row["results"] = {"error": str(e)}
        rows.append(row)
    return rows, label


def _player_effects_results(sec):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    ours = sim.basis()
    theirs = sim.basis(their)
    our_proj = sim.our_roster()
    their_proj = sim.our_roster(their)
    out_groups = []
    for group in sec["groups"]:
        gname = group["label"]
        if group["source"] == "their":
            raw = player_rows(ours, None, group["names"], their_proj)
            seat = "ours"
        else:
            raw = player_rows(theirs, their, group["names"], our_proj)
            seat = label
        players = [{"player": n, "dw": round(dw, 2), "dp_title": round(dt * 100, 1)}
                   for n, dw, dt in sorted(raw, key=lambda r: -r[1])]
        out_groups.append({"label": gname, "seat": seat, "players": players})
    return out_groups, label


def run_trade_screen(sec):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    our_proj = sim.our_roster()
    their_proj = sim.our_roster(their)
    before = sim.full_season()
    print("=== JOINT DEALS (%s) ===" % label)
    hdr = "label\tΔw us\tΔP(title) us\tΔw %s\tΔP(title) %s" % (label, label)
    print(hdr)
    for deal in sec["deals"]:
        name = deal.get("label") or "deal"
        try:
            dw_us, dt_us, dw_them, dt_them = price_deal(
                deal, their, our_proj, their_proj, before)
        except (KeyError, ValueError) as e:
            print("%s\tERROR\t%s" % (name, e))
            continue
        print("%s\t%+.2f\t%+.1f%%\t%+.2f\t%+.1f%%" % (
            name, dw_us, dt_us * 100, dw_them, dt_them * 100))


def player_rows(roster_full, path, names, from_rows):
    by = {p["n"]: p for p in from_rows}
    rows = []
    for n in names:
        body = by.get(n)
        if body is None:
            continue
        dw = sim.incoming_wins(roster_full, [body])[n][0]
        dt = sim.incoming_title(roster_full, [body], path=path)[n][0]
        rows.append((n, dw, dt))
    return rows


def run_player_effects(sec):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    ours = sim.basis()
    theirs = sim.basis(their)
    our_proj = sim.our_roster()
    their_proj = sim.our_roster(their)
    for group in sec["groups"]:
        gname = group["label"]
        if group["source"] == "their":
            rows = player_rows(ours, None, group["names"], their_proj)
            seat, who = "ours", label
        else:
            rows = player_rows(theirs, their, group["names"], our_proj)
            seat, who = label, "us"
        print("\n=== %s (%s on %s roster) ===" % (gname, who, seat))
        print("player\tΔw %s\tΔP(title)" % seat)
        for n, dw, dt in sorted(rows, key=lambda r: -r[1]):
            print("%s\t%+.2f\t%+.1f%%" % (n, dw, dt * 100))


def run_title_column(sec):
    their = resolve_roster(sec.get("their_roster"))
    include = sec.get("include") or ["ours", "their_incoming"]
    full = sim.basis()
    if "ours" in include:
        ours = sim.our_roster()
        print("OURS player_title")
        got = sim.player_title(full, [p["n"] for p in ours])
        for p in ours:
            m, sd, _ = got[p["n"]]
            print("%s\t%+.4f\t%.4f" % (p["n"], m, sd))
    if "their_incoming" in include and their:
        incoming = sim.our_roster(their)
        print("\nTHEIR_INCOMING incoming_title")
        got = sim.incoming_title(full, incoming)
        for p in incoming:
            m, sd, _ = got[p["n"]]
            print("%s\t%+.4f\t%.4f" % (p["n"], m, sd))
    if "roster_odds" in include:
        odds = sim.full_season()[sim.ROSTER]
        print("\nROSTER_ODDS")
        print("P_TITLE\t%.4f" % odds.title)
        print("PF\t%.0f" % odds.pf)
        print("WINS\t%.1f" % odds.wins)


def run_reports(sec):
    path = resolve_roster(sec.get("roster"))
    was = roster.ROSTER
    if path:
        roster.ROSTER = path
    try:
        for i, name in enumerate(sec["names"]):
            print(("\n" if i else "") + "=" * 72 + "\n"
                  + "%s  --  roster: %s\n" % (name.upper(), roster.label())
                  + "=" * 72)
            REPORTS[name]()
    finally:
        roster.ROSTER = was


_RUNNERS = {
    "reports": run_reports,
    "trade-screen": run_trade_screen,
    "player-effects": run_player_effects,
    "title-column": run_title_column,
}


def run_section(sec):
    validate_section(sec)
    _RUNNERS[sec["kind"]](sec)


def run_config(config):
    for sec in parse_config(config):
        run_section(sec)


def enrich_config(raw):
    if isinstance(raw, str):
        with open(raw) as f:
            raw = json.load(f)
    meta = {
        "simmed": date.today().isoformat(),
        "dp_title_note": TITLE_NOTE,
    }
    sections = parse_config(raw)
    enriched = []
    for sec in sections:
        sec = dict(sec)
        if sec["kind"] == "trade-screen":
            rows, label = _trade_screen_results(sec)
            by_label = {r["label"]: r.get("results") for r in rows}
            deals = []
            for deal in sec["deals"]:
                d = dict(deal)
                d["results"] = by_label.get(deal.get("label") or "deal")
                deals.append(d)
            sec["deals"] = deals
            sec["their_label"] = label
        elif sec["kind"] == "player-effects":
            groups, label = _player_effects_results(sec)
            sec["player_results"] = groups
            sec["their_label"] = label
        enriched.append(sec)
    if "sections" in raw:
        out = dict(raw)
        out["meta"] = meta
        out["sections"] = enriched
    else:
        out = enriched[0]
        out["meta"] = meta
    return out


def write_config(config_path, dest_path=None):
    with open(config_path) as f:
        raw = json.load(f)
    out = enrich_config(raw)
    path = dest_path or config_path
    with open(path, "w") as f:
        json.dump(out, f, indent=2)
        f.write("\n")
    return path


def check_config(config):
    for sec in parse_config(config):
        validate_section(sec)
