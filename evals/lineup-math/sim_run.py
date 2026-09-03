"""Run sim jobs from JSON config files."""
import json
import sys

from simlib.runner import KINDS, check_config, eval_columns_section, run_config, write_config


def usage():
    print("usage: ./run sim_run.py [--refresh] <config.json>")
    print("       ./run sim_run.py --eval <team_id>")
    print("       ./run sim_run.py --check <config.json>")
    print("       ./run sim_run.py --write <config.json> [dest.json]")
    print("")
    print("Team shape archive: evals/teams/<owner>/<Name> Trade Shapes.md")
    print("Run configs: $TMPDIR/ff-sim-<tag>.json (simlib.runner.sim_tmp_path)")
    print("Skips trade sections/deals that already have results; --refresh re-runs all.")
    print("Set \"refresh\": true on a section to re-run just that block.")
    print("--eval <team_id> prints counterparty eval columns in our seat.")
    print("")
    print("Kinds: %s" % ", ".join(KINDS))
    print("Schema: .claude/skills/sims/config.md")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        usage()
        sys.exit(0 if len(sys.argv) > 1 else 2)
    args = sys.argv[1:]
    force = False
    if args[0] == "--refresh":
        force = True
        args = args[1:]
    if not args:
        usage()
        sys.exit(2)
    if args[0] == "--eval":
        if len(args) != 2:
            usage()
            sys.exit(2)
        ref = int(args[1]) if args[1].isdigit() else args[1]
        try:
            run_config(eval_columns_section(ref))
        except (ValueError, KeyError, OSError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    if args[0] == "--check":
        if len(args) != 2:
            usage()
            sys.exit(2)
        try:
            check_config(args[1])
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    if args[0] == "--write":
        if len(args) not in (2, 3):
            usage()
            sys.exit(2)
        dest = args[2] if len(args) == 3 else None
        try:
            path = write_config(args[1], dest)
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        print(path)
        sys.exit(0)
    try:
        run_config(args[0], force=force)
    except (ValueError, KeyError, OSError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
