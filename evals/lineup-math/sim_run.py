"""Run sim jobs from JSON config files."""
import json
import sys

from simlib.runner import KINDS, check_config, run_config, write_config


def usage():
    print("usage: ./run sim_run.py <config.json>")
    print("       ./run sim_run.py --check <config.json>")
    print("       ./run sim_run.py --write <config.json> [dest.json]")
    print("")
    print("Kinds: %s" % ", ".join(KINDS))
    print("Schema: .claude/skills/sims/config.md")


if __name__ == "__main__":
    if len(sys.argv) < 2 or sys.argv[1] in ("-h", "--help", "help"):
        usage()
        sys.exit(0 if len(sys.argv) > 1 else 2)
    if sys.argv[1] == "--check":
        if len(sys.argv) != 3:
            usage()
            sys.exit(2)
        try:
            check_config(sys.argv[2])
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        sys.exit(0)
    if sys.argv[1] == "--write":
        if len(sys.argv) not in (3, 4):
            usage()
            sys.exit(2)
        dest = sys.argv[3] if len(sys.argv) == 4 else None
        try:
            path = write_config(sys.argv[2], dest)
        except (ValueError, KeyError, OSError, json.JSONDecodeError) as e:
            print(e, file=sys.stderr)
            sys.exit(1)
        print(path)
        sys.exit(0)
    try:
        run_config(sys.argv[1])
    except (ValueError, KeyError, OSError) as e:
        print(e, file=sys.stderr)
        sys.exit(1)
