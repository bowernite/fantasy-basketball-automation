"""Offline guard for the extension watcher. Fake build and notifier; no launchd, no Safari."""
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import extension_watch


def setup(build_ok=True):
    tmp = tempfile.mkdtemp()
    inputs = os.path.join(tmp, "overrides.json")
    with open(inputs, "w") as f:
        f.write("{}")
    builds, notices = [], []

    def build():
        builds.append(open(inputs).read())
        return build_ok

    watcher = extension_watch.Watcher(
        paths=lambda: [inputs], build=build, notify=lambda *msg: notices.append(msg),
        state=os.path.join(tmp, "state"), quiet=15)
    return watcher, inputs, builds, notices


def edit(path, text):
    with open(path, "w") as f:
        f.write(text)


class Watch(unittest.TestCase):
    def test_an_unbuilt_input_set_builds_once_after_the_quiet_window(self):
        watcher, _, builds, _ = setup()
        watcher.poll(now=0)
        watcher.poll(now=10)
        self.assertEqual(builds, [])
        watcher.poll(now=15)
        watcher.poll(now=20)
        watcher.poll(now=40)
        self.assertEqual(builds, ["{}"])

    def test_a_burst_of_edits_builds_once_from_the_last_edit(self):
        watcher, inputs, builds, _ = setup()
        watcher.poll(now=0)
        watcher.poll(now=20)
        for second, text in [(30, "a"), (40, "ab"), (50, "abc")]:
            edit(inputs, text)
            watcher.poll(now=second)
        watcher.poll(now=60)
        self.assertEqual(builds, ["{}"])
        watcher.poll(now=65)
        watcher.poll(now=90)
        self.assertEqual(builds, ["{}", "abc"])

    def test_rewriting_an_input_with_the_same_content_does_not_rebuild(self):
        watcher, inputs, builds, _ = setup()
        watcher.poll(now=0)
        watcher.poll(now=20)
        edit(inputs, "{}")
        watcher.poll(now=30)
        watcher.poll(now=60)
        self.assertEqual(builds, ["{}"])

    def test_a_failed_build_notifies_once_and_waits_for_the_next_edit(self):
        watcher, inputs, builds, notices = setup(build_ok=False)
        for second in range(0, 120, 5):
            watcher.poll(now=second)
        self.assertEqual(builds, ["{}"])
        self.assertEqual(len(notices), 1)
        self.assertIn("failed", notices[0][0])
        edit(inputs, "fixed")
        watcher.poll(now=120)
        watcher.poll(now=140)
        self.assertEqual(builds, ["{}", "fixed"])

    def test_inputs_returning_to_a_once_failed_state_rebuild_after_a_later_success(self):
        watcher, inputs, builds, _ = setup()
        results = iter([False, True, True])
        watcher.build = lambda: builds.append(open(inputs).read()) or next(results)
        for text, second in [("x", 0), ("y", 100), ("x", 200)]:
            edit(inputs, text)
            watcher.poll(now=second)
            watcher.poll(now=second + 20)
        self.assertEqual(builds, ["x", "y", "x"])

    def test_an_input_that_cannot_be_listed_yet_waits_instead_of_crashing(self):
        watcher, _, builds, _ = setup()

        def no_pool_file():
            raise FileNotFoundError("players-*.json")

        watcher.paths = no_pool_file
        watcher.poll(now=0)
        watcher.poll(now=20)
        self.assertEqual(builds, [])

    def test_a_successful_build_notifies_that_the_extension_is_live(self):
        watcher, _, _, notices = setup()
        watcher.poll(now=0)
        watcher.poll(now=20)
        self.assertEqual(len(notices), 1)
        self.assertIn("updated", notices[0][0])

    def test_a_restarted_watcher_does_not_rebuild_what_is_already_installed(self):
        watcher, inputs, builds, _ = setup()
        watcher.poll(now=0)
        watcher.poll(now=20)
        restarted = extension_watch.Watcher(
            paths=watcher.paths, build=watcher.build, notify=watcher.notify,
            state=watcher.state, quiet=15)
        restarted.poll(now=100)
        restarted.poll(now=200)
        self.assertEqual(builds, ["{}"])

    def test_an_input_vanishing_mid_write_waits_instead_of_crashing(self):
        watcher, inputs, builds, _ = setup()
        paths = [inputs]
        watcher.paths = lambda: paths
        watcher.poll(now=0)
        paths.append(inputs + ".gone")
        watcher.poll(now=20)
        paths.pop()
        watcher.poll(now=40)
        watcher.poll(now=60)
        self.assertEqual(builds, ["{}"])


if __name__ == "__main__":
    unittest.main()
