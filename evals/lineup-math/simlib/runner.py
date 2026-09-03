"""Run sim jobs from JSON config. See `.claude/skills/sims/config.md`."""
import json
import os
import re
import tempfile
from datetime import date

import sim
from fetch_data import SEASON_TAG, TEAM, season_dw_tag
from simlib import roster
from simlib.data import HERE
from simlib.reports import OURS_ONLY, REPORTS

_BASE_CACHE = {}

KINDS = ("reports", "trade-screen", "player-effects", "title-column",
         "eval-columns")
WRITEBACK_KINDS = frozenset(("trade-screen", "player-effects"))

TEAM_SLUG = {
    161025: "my-team",
    161016: "bonin",
    161024: "josh",
    161014: "chris",
    161018: "brian",
    161017: "joe",
    161021: "hlina",
    160941: "matthew",
    161019: "henry",
    161015: "jon",
    161020: "mitch",
    161022: "todd",
}

TEAM_SIM_LABEL = {
    "my-team": "My Team",
    "bonin": "Bonin",
    "josh": "Josh",
    "chris": "Chris",
    "brian": "Brian",
    "joe": "Joe",
    "hlina": "Hlina",
    "matthew": "Matthew",
    "henry": "Henry",
    "jon": "Jon",
    "mitch": "Mitch",
    "todd": "Todd",
}


def team_trade_shapes_path(owner):
    if isinstance(owner, int) or (isinstance(owner, str) and owner.isdigit()):
        slug = TEAM_SLUG[int(owner)]
    else:
        slug = str(owner)
    label = TEAM_SIM_LABEL.get(slug, slug.title())
    return os.path.join(HERE, "..", "teams", slug, "%s Trade Shapes.md" % label)


def team_sims_path(owner):
    return team_trade_shapes_path(owner)


def team_sim_path(owner):
    return team_trade_shapes_path(owner)


def sim_tmp_path(tag):
    safe = re.sub(r"[^\w.-]+", "-", str(tag).strip()).strip("-") or "run"
    return os.path.join(tempfile.gettempdir(), "ff-sim-%s.json" % safe)


def eval_columns_section(team_ref):
    return {"kind": "eval-columns", "their_roster": team_ref}


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
    elif kind == "eval-columns":
        if not sec.get("their_roster"):
            raise ValueError("eval-columns needs 'their_roster'")
        path = resolve_roster(sec["their_roster"])
        if os.path.basename(path) == os.path.basename(roster.OURS):
            raise ValueError("eval-columns is counterparty columns; "
                             "sim.py players weeks and player_title for ours")


def bodies(names, roster_rows):
    by = {p["n"]: p for p in roster_rows}
    missing = [n for n in names if n not in by]
    if missing:
        raise KeyError("missing on roster: %s" % ", ".join(missing))
    return [by[n] for n in names]


TITLE_NOTE = "both rosters change in the 12-team field"


def _simmed_date(when=None):
    d = when or date.today()
    return "%d/%d/%d" % (d.month, d.day, d.year % 100)


def price_deal(deal, their, our_proj, their_proj, before=None):
    after_ours = sim.basis_after_trade(
        roster.OURS, deal["out_us"], bodies(deal["in_from_them"], their_proj))
    after_theirs = sim.basis_after_trade(
        their, deal["out_them"], bodies(deal["in_from_us"], our_proj))
    after_us, before_us, after_them, before_them = sim.deal_odds(
        after_ours, after_theirs, their, before=before)
    in_us = bodies(deal["in_from_them"], their_proj)
    out_us = bodies(deal["out_us"], our_proj)
    in_them = bodies(deal["in_from_us"], our_proj)
    out_them = bodies(deal["out_them"], their_proj)
    fdw_us = sim.deal_formula_wins(in_us, out_us)
    fdw_them = sim.deal_formula_wins(in_them, out_them)
    return (after_us.wins - before_us.wins, after_us.title - before_us.title,
            after_them.wins - before_them.wins,
            after_them.title - before_them.title,
            fdw_us, fdw_them)


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


def _team_id(their_roster):
    if their_roster == "us":
        return TEAM
    if isinstance(their_roster, int):
        return their_roster
    s = str(their_roster).strip()
    if s.isdigit():
        return int(s)
    name = os.path.basename(resolve_roster(s))
    parts = name.replace(".json", "").split("-")
    if len(parts) >= 2 and parts[1].isdigit():
        return int(parts[1])
    raise ValueError("no team eval for %s" % their_roster)


def eval_md_for(their_roster):
    tid = _team_id(their_roster)
    slug = TEAM_SLUG.get(tid)
    if slug is None:
        raise ValueError("no team eval for %s" % their_roster)
    folder = os.path.join(HERE, "..", "teams", slug)
    if not os.path.isdir(folder):
        return None
    matches = [f for f in os.listdir(folder)
               if f.endswith("Team.md") and "Trade" not in f]
    if len(matches) != 1:
        return None
    return os.path.join(folder, matches[0])


def deal_delta_base(deal, their_roster):
    their_path = eval_md_for(their_roster)
    our_path = eval_md_for(TEAM)
    if not their_path or not our_path:
        return None
    try:
        out = _player_base(deal["out_us"], our_path)
        inc = _player_base(deal["in_from_them"], their_path)
        out += int(deal.get("out_us_extra_base") or 0)
        inc += int(deal.get("in_from_us_extra_base") or 0)
        return inc - out
    except KeyError:
        return None


def _deal_key(deal):
    return deal.get("label") or "deal"


def _deals_needing_run(sec, force=False):
    if force or sec.get("refresh"):
        return sec["deals"]
    return [d for d in sec["deals"] if "results" not in d]


def _trade_screen_results(sec, deals=None):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    our_proj = sim.our_roster(roster.OURS)
    their_proj = sim.our_roster(their)
    before = sim.full_season()
    rows = []
    for deal in deals if deals is not None else sec["deals"]:
        name = deal.get("label") or "deal"
        row = {"label": name}
        try:
            dw_us, dt_us, dw_them, dt_them, fdw_us, fdw_them = price_deal(
                deal, their, our_proj, their_proj, before)
            row["results"] = {
                "delta_base_us": deal_delta_base(deal, sec["their_roster"]),
                "fdw_us": round(fdw_us, 2),
                "dw_us": round(dw_us, 2),
                "dp_title_us": round(dt_us * 100, 1),
                "fdw_them": round(fdw_them, 2),
                "dw_them": round(dw_them, 2),
                "dp_title_them": round(dt_them * 100, 1),
                "dp_title_note": TITLE_NOTE,
                "simmed": _simmed_date(),
            }
        except (KeyError, ValueError) as e:
            row["results"] = {
                "error": str(e),
                "simmed": _simmed_date(),
            }
        rows.append(row)
    return rows, label


def _player_effects_results(sec):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    ours = sim.basis(roster.OURS)
    theirs = sim.basis(their)
    our_proj = sim.our_roster(roster.OURS)
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
        players = [{"player": n, "fdw": round(fdw, 2), "dw": round(dw, 2),
                    "dp_title": round(dt * 100, 1)}
                   for n, fdw, dw, dt in sorted(raw, key=lambda r: -r[2])]
        out_groups.append({"label": gname, "seat": seat, "players": players})
    return out_groups, label


def _print_trade_screen(rows, label):
    print("=== JOINT DEALS (%s) ===" % label)
    stag = season_dw_tag()
    hdr = ("label\tΔBASE us\tΔw us\tΔw %s us\tΔP(title) us\t"
           "Δw %s\tΔw %s %s\tΔP(title) %s"
           % (stag, stag, stag, label, label))
    print(hdr)
    for row in rows:
        name = row["label"]
        res = row.get("results") or {}
        if "error" in res:
            print("%s\tERROR\t%s" % (name, res["error"]))
            continue
        base = res.get("delta_base_us")
        base_s = "%+d" % base if base is not None else "–"
        print("%s\t%s\t%+.2f\t%+.2f\t%+.1f%%\t%+.2f\t%+.2f\t%+.1f%%" % (
            name, base_s,
            res["fdw_us"], res["dw_us"], res["dp_title_us"],
            res["fdw_them"], res["dw_them"], res["dp_title_them"]))


def _merge_trade_screen(sec, rows, label):
    by_label = {r["label"]: r.get("results") for r in rows}
    deals = []
    for deal in sec["deals"]:
        d = dict(deal)
        key = _deal_key(deal)
        if key in by_label:
            d["results"] = by_label[key]
        deals.append(d)
    sec["deals"] = deals
    sec["their_label"] = label
    sec["meta"] = _meta()
    sec.pop("refresh", None)
    return sec


def _run_trade_screen(sec, force=False):
    sec = dict(sec)
    pending = _deals_needing_run(sec, force)
    if not pending:
        return sec, False
    rows, label = _trade_screen_results(sec, pending)
    _print_trade_screen(rows, label)
    return _merge_trade_screen(sec, rows, label), True


def player_rows(roster_full, path, names, from_rows):
    by = {p["n"]: p for p in from_rows}
    missing = [n for n in names if n not in by]
    if missing:
        raise KeyError("missing on roster: %s" % ", ".join(missing))
    rows = []
    for n in names:
        body = by[n]
        fdw = sim.formula_player_wins(body)
        dw = sim.incoming_wins(roster_full, [body])[n][0]
        seat = path if path is not None else roster.OURS
        dt = sim.incoming_title(roster_full, [body], path=seat)[n][0]
        rows.append((n, fdw, dw, dt))
    return rows


def _print_player_effects(groups, sec):
    their = resolve_roster(sec["their_roster"])
    label = sec.get("their_label") or their
    for group in sec["groups"]:
        gname = group["label"]
        match = next(g for g in groups if g["label"] == gname)
        seat = match["seat"]
        if group["source"] == "their":
            who = label
        else:
            who = "us"
        print("\n=== %s (%s on %s roster) ===" % (gname, who, seat))
        print("player\tΔw\tΔw %s\tΔP(title)" % season_dw_tag())
        for row in match["players"]:
            print("%s\t%+.2f\t%+.2f\t%+.1f%%" % (
                row["player"], row["fdw"], row["dw"], row["dp_title"]))


def _player_effects_needs_run(sec, force=False):
    if force or sec.get("refresh"):
        return True
    return "player_results" not in sec


def _merge_player_effects(sec, groups, label):
    sec["player_results"] = groups
    sec["their_label"] = label
    sec.pop("refresh", None)
    return sec


def _run_player_effects(sec, force=False):
    sec = dict(sec)
    if not _player_effects_needs_run(sec, force):
        return sec, False
    groups, label = _player_effects_results(sec)
    _print_player_effects(groups, sec)
    return _merge_player_effects(sec, groups, label), True


def run_title_column(sec):
    their = resolve_roster(sec.get("their_roster"))
    include = sec.get("include") or ["ours", "their_incoming"]
    full = sim.basis(roster.OURS)
    if "ours" in include:
        ours = sim.our_roster(roster.OURS)
        print("OURS player_title")
        got = sim.player_title(full, [p["n"] for p in ours], path=roster.OURS)
        for p in ours:
            m, sd, _ = got[p["n"]]
            print("%s\t%+.4f\t%.4f" % (p["n"], m, sd))
    if "their_incoming" in include and their:
        incoming = sim.our_roster(their)
        print("\nTHEIR_INCOMING incoming_title")
        got = sim.incoming_title(full, incoming, path=roster.OURS)
        for p in incoming:
            m, sd, _ = got[p["n"]]
            print("%s\t%+.4f\t%.4f" % (p["n"], m, sd))
    if "roster_odds" in include:
        odds = sim.full_season()[roster.OURS]
        print("\nROSTER_ODDS")
        print("P_TITLE\t%.4f" % odds.title)
        print("PF\t%.0f" % odds.pf)
        print("WINS\t%.1f" % odds.wins)


def run_eval_columns(sec):
    from simlib.eval_columns import print_eval_columns
    print_eval_columns(resolve_roster(sec["their_roster"]), sec.get("names"))


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
    "title-column": run_title_column,
    "eval-columns": run_eval_columns,
}


def _load_config(config):
    if isinstance(config, str):
        with open(config) as f:
            return json.load(f)
    return config


def _meta():
    return {"simmed": _simmed_date(), "dp_title_note": TITLE_NOTE}


def _pack_config(raw, sections):
    if "sections" in raw:
        out = dict(raw)
        out["sections"] = sections
    else:
        out = sections[0]
    out["meta"] = _meta()
    return out


def _enrich_section(sec, force=False):
    sec = dict(sec)
    validate_section(sec)
    kind = sec["kind"]
    if kind == "trade-screen":
        pending = _deals_needing_run(sec, force)
        if not pending:
            return sec
        rows, label = _trade_screen_results(sec, pending)
        return _merge_trade_screen(sec, rows, label)
    if kind == "player-effects":
        if not _player_effects_needs_run(sec, force):
            return sec
        groups, label = _player_effects_results(sec)
        return _merge_player_effects(sec, groups, label)
    return sec


def run_section(sec, force=False):
    sec = dict(sec)
    validate_section(sec)
    kind = sec["kind"]
    if kind == "trade-screen":
        return _run_trade_screen(sec, force)
    if kind == "player-effects":
        return _run_player_effects(sec, force)
    _RUNNERS[kind](sec)
    return sec, True


def run_config(config, write_back=None, force=False):
    config_path = config if isinstance(config, str) else None
    raw = _load_config(config)
    sections = parse_config(raw)
    if write_back is None:
        write_back = (config_path is not None
                      and any(s.get("kind") in WRITEBACK_KINDS for s in sections))
    out_sections = []
    changed = False
    for sec in sections:
        out_sec, ran = run_section(sec, force)
        changed = changed or ran
        out_sections.append(out_sec)
    if write_back and config_path and (changed or force):
        out = _pack_config(raw, out_sections)
        with open(config_path, "w") as f:
            json.dump(out, f, indent=2)
            f.write("\n")
    return out_sections


def enrich_config(raw, force=True):
    raw = _load_config(raw)
    sections = []
    for sec in parse_config(raw):
        if sec.get("kind") in WRITEBACK_KINDS:
            sections.append(_enrich_section(sec, force))
        else:
            sections.append(dict(sec))
    return _pack_config(raw, sections)


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
