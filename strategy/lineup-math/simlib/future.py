"""League roll-forward: every roster aged together along progression paths,
with exits, drafts off the real pick ledger and cuts to 38, season by season."""
import random, zlib
from fetch_data import LIVE_SEASON
from . import bracket, engine, progression as prog, shard, title
from .roster import pad
from .roster import MAX_WIRE as MAX_BODIES
from .score import SCORE_FDW
from .value import formula_player_wins

ROUNDS = 4

TOP_FOUR = 4
LOTTERY = (0.50, 0.25, 0.15, 0.10)   # worst first; only 1.01 is drawn


def simulate(start, teams1, ledger, template, paths, seed, years, t_eng, t_in):
    """One run per path: `start` is {team path: [{row, pl, base}]} (pl None
    plays season 1 only), `teams1` is `season_one(start)`. Per path, ([{team:
    PF}] by season, [{team: P(title)}] from season 2, [{team: flow}] by
    offseason)"""
    job = (start, teams1, ledger, template, seed, years, t_eng, t_in)
    nw = shard.n_workers(None, paths, floor=8)
    if nw > 1:
        shard.retire()  # a pool that already served engine.run hangs on a new job shape
    parts = shard.mapped(_chunk, [(s, c) + job for s, c in shard.chunks(paths, nw)], nw)
    return [run for part in parts for run in part]


def _chunk(job):
    first, count, start, teams1, ledger, template, seed, years, t_eng, t_in = job
    return [_path("%d/%d" % (seed, p), start, teams1, ledger, template, years, t_eng, t_in)
            for p in range(first, first + count)]


def _path(key, start, teams1, ledger, template, years, t_eng, t_in):
    sampler = prog.Sampler(prog.params())
    league = {t: [player(e, sampler, key, years) for e in entries] for t, entries in start.items()}
    teams, pfs, titles, flows = teams1, [{t.path: t.pf for t in teams1}], [], []
    for s in range(years - 1):
        standings = title.sampled_standings(teams, "%s/season/%d" % (key, s))
        league, flow = offseason(league, s, standings, ledger, template, key, years)
        teams = tuple(_measure(league[t.path], s + 1, t.path, t_eng) for t in teams1)
        odds = title.season_run(teams, trials=t_in, seed0=zlib.crc32(("%s/title/%d" % (key, s)).encode()),
                                workers=1)[0]
        for t in teams1:
            flow[t.path]["drafted_fp"] = _drafted_share(league[t.path], s + 1)
        pfs.append({t.path: t.pf for t in teams})
        titles.append({t.path: odds[t.path].title for t in teams})
        flows.append(flow)
    return pfs, titles, flows


def player(e, sampler, key, years):
    row = e["row"]
    if e["pl"] is None:
        rates, gps = [row["avg"]] + [None] * (years - 1), [row["gp"]] + [0.0] * (years - 1)
    else:
        gp1 = _gp1(e["pl"], row["gp"], sampler)
        rates, gps = sampler.path(dict(e["pl"], gp1=gp1), years, random.Random("%s/%s" % (key, row["n"])))
        rates[0], gps[0] = row["avg"], gp1
    return {"n": row["n"], "tm": row["tm"], "elig": list(row["elig"]), "base": e["base"],
            "rates": rates, "gps": gps}


def _drafted_share(roster, s):
    """Share of the top 12 bodies' season FP held by rookies drafted in this roll"""
    fp = sorted(((p["rates"][s] * p["gps"][s], p["n"].startswith("'")) for p in roster), reverse=True)[:12]
    return sum(x for x, drafted in fp if drafted) / (sum(x for x, _ in fp) or 1.0)


def season_one(start):
    """Season 1's 12 teams, measured as `title` measures them but on `_gp1`"""
    sampler = prog.Sampler(prog.params())
    return tuple(bracket.measure(pad([dict(e["row"], gp=int(round(_gp1(e["pl"], e["row"]["gp"], sampler)))) for e in es]), path)
                 for path, es in sorted(start.items()))


def _gp1(pl, gp, sampler):
    """Season 1's GP on the model's basis, the one every later season is on:
    the projection, capped at the model's forecast off last season (a
    draftee's off a norm season). The projection stands after a season lost
    to injury, since it knows the return and the model doesn't"""
    if pl is None or gp < prog.ACTIVE:
        return gp
    if pl["gp_last"] is not None and pl["gp_last"] < prog.ACTIVE:
        return gp
    last = sampler.gp_ref if pl["gp_last"] is None else pl["gp_last"]
    return min(gp, sampler.gp_expected(last, pl["age1"] - 1, pl["rate1"]))


def _measure(roster, s, path, trials):
    rows = pad([{"n": p["n"], "tm": p["tm"], "avg": p["rates"][s], "gp": int(round(p["gps"][s])),
                 "elig": p["elig"]} for p in roster])
    res = engine.run(rows, trials=trials, workers=1)
    return bracket.Team(path, res["pf"], bracket.reg_weeks(res["wk"]),
                        bracket.bracket_weeks(rows, trials=trials, workers=1))


def draft_order(standings, rng):
    """Teams by slot, 1.01 first, from `standings` (best record first): the
    top 4 pick 12..9, the rest worst-first, then the worst 4 draw for 1.01"""
    order = list(reversed(standings[TOP_FOUR:])) + list(reversed(standings[:TOP_FOUR]))
    x, drawn = rng.random(), len(LOTTERY) - 1
    for i, odds in enumerate(LOTTERY):
        x -= odds
        if x < 0:
            drawn = i
            break
    return [order[drawn]] + order[:drawn] + order[drawn + 1:]


def offseason(league, s, standings, ledger, template, key, years):
    """{team: roster} in season `s` -> season `s` + 1: exits leave, then the
    draft held after season `s`. A pick's slot follows its original team's
    finish; the rookie joins whoever holds it (`ledger`, own if absent)"""
    year = LIVE_SEASON + 1 + s
    order = draft_order(standings, random.Random("%s/lottery/%d" % (key, s)))
    sampler = prog.Sampler(prog.params())
    out = {t: [p for p in roster if p["rates"][s + 1] is not None] for t, roster in league.items()}
    flow = {t: {"exits": len(league[t]) - len(out[t]), "picks": [], "rookies": 0, "cuts": 0}
            for t in league}
    for rnd in range(1, ROUNDS + 1):
        for slot, owner in enumerate(order, 1):
            ordinal = (rnd - 1) * len(order) + slot
            holder = ledger.get((year, rnd, owner), owner)
            flow[holder]["picks"].append((rnd, slot))
            out[holder].append(_draftee(template[ordinal - 1], "'%02d %d.%02d" % (year % 100, rnd, slot),
                                        s, years, sampler, key))
    for t, roster in out.items():
        kept = _cut(roster, s)
        flow[t]["cuts"] = len(roster) - len(kept)
        flow[t]["rookies"] = sum(1 for p in kept if p["rates"][s] is None)
        out[t] = kept
    return out, flow


def _cut(roster, s):
    """Down to 38 by Score's static partial -- BASE + formula Δw on the latest
    season, a draftee's on his first. Sim terms need a sim per candidate"""
    over = len(roster) - MAX_BODIES
    if over <= 0:
        return roster

    def partial(p):
        t = s if p["rates"][s] is not None else s + 1
        return p["base"] + SCORE_FDW * formula_player_wins({"n": p["n"], "avg": p["rates"][t],
                                                            "gp": p["gps"][t]})
    gone = {id(p) for p in sorted(roster, key=partial)[:over]}
    return [p for p in roster if id(p) not in gone]


def _draftee(tpl, label, s, years, sampler, key):
    gp1 = _gp1(tpl, tpl["gp1"], sampler)
    rates, gps = sampler.path(dict(tpl, name=label, gp1=gp1), years - s - 1, random.Random("%s/%s" % (key, label)))
    return {"n": label, "tm": tpl["tm"], "elig": list(tpl["elig"]), "base": tpl["base"],
            "rates": [None] * (s + 1) + rates, "gps": [0.0] * (s + 1) + gps}
