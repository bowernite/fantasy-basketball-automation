"""Rebuild + reinstall the Safari extension whenever its projection inputs change.

    python3 .claude/skills/projections/extension_watch.py install    # launchd agent, starts now and at login
    python3 .claude/skills/projections/extension_watch.py uninstall
    python3 .claude/skills/projections/extension_watch.py watch      # foreground; what the agent runs

`SKILL.md` §Browser extension owns the details.
"""
import datetime
import hashlib
import os
import plistlib
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import extension_data

REPO = os.path.realpath(os.path.join(HERE, os.pardir, os.pardir, os.pardir))
STATE = os.path.join(REPO, ".safari", "extension-watch-state")
LOG = os.path.expanduser("~/Library/Logs/ff-extension-watch.log")
LABEL = "dev.abramczyk.ff-extension-watch"
PLIST = os.path.expanduser("~/Library/LaunchAgents/%s.plist" % LABEL)
POLL_SECONDS = 5
QUIET_SECONDS = 15


class Watcher:
    def __init__(self, paths, build, notify, state, quiet):
        self.paths, self.build, self.notify = paths, build, notify
        self.state, self.quiet = state, quiet
        self.built, self.failed = read_state(state), None
        self.pending, self.pending_since = None, None

    def poll(self, now):
        try:
            current = fingerprint(self.paths())
        except FileNotFoundError:
            self.pending = None
            return
        if current in (self.built, self.failed):
            self.pending = None
            return
        if current != self.pending:
            self.pending, self.pending_since = current, now
            return
        if now - self.pending_since < self.quiet:
            return
        if self.build():
            self.built = current
            with open(self.state, "w") as f:
                f.write(current)
            self.notify("Extension updated", "Reload Fleaflicker to see the new projections")
        else:
            self.failed = current
            self.notify("Extension rebuild failed", "Click for the log; fix the input and save again")


def read_state(path):
    if not os.path.isfile(path):
        return None
    with open(path) as f:
        return f.read()


def fingerprint(paths):
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.encode())
        with open(path, "rb") as f:
            digest.update(f.read())
    return digest.hexdigest()


def watch():
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    watcher = Watcher(paths=extension_data.input_paths, build=build_extension,
                      notify=notify, state=STATE, quiet=QUIET_SECONDS)
    log("watching %d inputs" % len(extension_data.input_paths()))
    while True:
        watcher.poll(time.monotonic())
        time.sleep(POLL_SECONDS)


def build_extension():
    log("inputs changed -> bun run safari:dev")
    result = subprocess.run(["bun", "run", "safari:dev"], cwd=REPO, text=True,
                            env=dict(os.environ, SKIP_CLIPBOARD="1"),
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    print(result.stdout, end="", flush=True)
    log("build exited %d" % result.returncode)
    return result.returncode == 0


def notify(title, message):
    log("%s: %s" % (title, message))
    if shutil.which("terminal-notifier"):
        subprocess.run(["terminal-notifier", "-title", title, "-message", message,
                        "-group", LABEL, "-open", "file://" + LOG])
    else:
        subprocess.run(["osascript", "-e", 'display notification "%s" with title "%s"' % (message, title)])


def install():
    tool_dirs = [os.path.dirname(shutil.which(tool)) for tool in ("bun", "python3", "terminal-notifier")
                 if shutil.which(tool)]
    path = ":".join(dict.fromkeys(tool_dirs + ["/usr/bin", "/bin", "/usr/sbin", "/sbin"]))
    agent = {
        "Label": LABEL,
        "ProgramArguments": [shutil.which("python3"), os.path.abspath(__file__), "watch"],
        "WorkingDirectory": REPO,
        "EnvironmentVariables": {"PATH": path},
        "RunAtLoad": True,
        "KeepAlive": True,
        "StandardOutPath": LOG,
        "StandardErrorPath": LOG,
    }
    unload()
    os.makedirs(os.path.dirname(PLIST), exist_ok=True)
    with open(PLIST, "wb") as f:
        plistlib.dump(agent, f)
    subprocess.run(["launchctl", "bootstrap", "gui/%d" % os.getuid(), PLIST], check=True)
    print("installed %s; log: %s" % (LABEL, LOG))


def uninstall():
    unload()
    if os.path.exists(PLIST):
        os.remove(PLIST)
    print("uninstalled %s" % LABEL)


def unload():
    subprocess.run(["launchctl", "bootout", "gui/%d/%s" % (os.getuid(), LABEL)],
                   stderr=subprocess.DEVNULL)


def log(message):
    print("%s %s" % (datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), message), flush=True)


if __name__ == "__main__":
    commands = {"watch": watch, "install": install, "uninstall": uninstall}
    if len(sys.argv) != 2 or sys.argv[1] not in commands:
        sys.exit("usage: extension_watch.py {%s}" % ",".join(commands))
    commands[sys.argv[1]]()
