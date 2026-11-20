"""contribute.sh against local repos: a fake `gh` and file:// remotes stand in for GitHub."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import fixtures

SCRIPT = fixtures.SCRIPTS / "contribute.sh"
FAKE_GH = """#!/bin/sh
echo "gh $*" >> "$FAKE_GH_LOG"
case "$1 $2" in
  "api user") [ -n "$FAKE_GH_LOGIN" ] || exit 1; echo "$FAKE_GH_LOGIN" ;;
  "pr create") [ -z "$FAKE_GH_FAIL_PR" ] || exit 1; echo "https://github.com/DominikKriss/mixing-console-skills/pull/99" ;;
  "pr list") [ -z "$FAKE_GH_PR_OPEN" ] || echo "https://github.com/DominikKriss/mixing-console-skills/pull/98" ;;
esac
exit 0
"""


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True, text=True).stdout


@unittest.skipUnless(shutil.which("bash") and shutil.which("git"), "needs bash and git")
class Contribute(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.hub = root / "hub"
        upstream = self.hub / "DominikKriss" / "mixing-console-skills.git"
        upstream.parent.mkdir(parents=True)
        seed = root / "seed"
        (seed / "lv1-session" / "scripts").mkdir(parents=True)
        shutil.copy(SCRIPT, seed / "lv1-session" / "scripts" / "contribute.sh")
        (seed / "lv1-session" / "SKILL.md").write_text("skill\n")
        (seed / "README.md").write_text("readme\n")
        (seed / ".gitignore").write_text("*.emo\n")
        self.env = dict(os.environ, GIT_CONFIG_GLOBAL=str(root / "gitconfig"), GIT_CONFIG_NOSYSTEM="1",
                        FAKE_GH_LOG=str(root / "gh.log"), FAKE_GH_LOGIN="DominikKriss",
                        PATH=f"{root / 'bin'}{os.pathsep}{os.environ['PATH']}")
        (root / "gitconfig").write_text(
            f'[user]\n  name = Test\n  email = test@example.com\n[init]\n  defaultBranch = main\n'
            f'[url "file://{self.hub}/"]\n  insteadOf = https://github.com/\n')
        (root / "bin").mkdir()
        (root / "bin" / "gh").write_text(FAKE_GH)
        (root / "bin" / "gh").chmod(0o755)
        os.environ_backup = os.environ.copy()
        os.environ.update(self.env)
        git(root, "init", "-q", "--bare", str(upstream))
        git(seed, "init", "-q")
        git(seed, "add", "-A")
        git(seed, "commit", "-q", "-m", "seed")
        git(seed, "push", "-q", str(upstream), "HEAD:main")
        self.clone = root / "clone"
        git(root, "clone", "-q", "https://github.com/DominikKriss/mixing-console-skills.git", str(self.clone))
        self.skill = self.clone / "lv1-session"
        self.body = root / "body.md"
        self.body.write_text("body\n")
        self.log = Path(self.env["FAKE_GH_LOG"])
        self.upstream = upstream

    def tearDown(self):
        os.environ.clear()
        os.environ.update(os.environ_backup)
        self.tmp.cleanup()

    def run_script(self, *extra, login="DominikKriss", **env_extra):
        env = dict(self.env, FAKE_GH_LOGIN=login, **env_extra)
        return subprocess.run(["bash", str(self.skill / "scripts" / "contribute.sh"), "--title", "Fix a thing",
                               "--body-file", str(self.body), *extra], env=env, capture_output=True, text=True)

    def test_dry_run_lists_files_and_changes_nothing(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        r = self.run_script("--dry-run")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("GitHub account : DominikKriss", r.stdout)
        self.assertIn("lv1-session/SKILL.md", r.stdout)
        self.assertEqual(git(self.clone, "rev-parse", "--abbrev-ref", "HEAD").strip(), "main")
        self.assertFalse(self.log.exists() and "pr create" in self.log.read_text())

    def test_no_changes(self):
        self.assertEqual(self.run_script("--dry-run").returncode, 1)

    def test_not_logged_in(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        self.assertEqual(self.run_script("--dry-run", login="").returncode, 3)

    def test_scene_file_with_accented_name_is_refused(self):
        (self.skill / "Bänd.scn").write_text("/ch/01/config\n")
        r = self.run_script("--dry-run")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)

    def test_staged_file_outside_the_skill_is_refused(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        (self.clone / "README.md").write_text("private note\n")
        git(self.clone, "add", "README.md")
        r = self.run_script("--dry-run")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
        self.assertIn("README.md", r.stderr)

    def test_unpushed_local_commit_is_refused(self):
        (self.clone / "README.md").write_text("local\n")
        git(self.clone, "commit", "-qam", "local")
        (self.skill / "SKILL.md").write_text("skill v2\n")
        r = self.run_script("--dry-run")
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)

    def test_maintainer_pushes_a_branch_and_opens_the_pr(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        r = self.run_script()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("learn/fix-a-thing", git(self.upstream, "branch", "--list"))
        files = git(self.upstream, "show", "--name-only", "--format=", "learn/fix-a-thing").split()
        self.assertEqual(files, ["lv1-session/SKILL.md"])
        log = self.log.read_text()
        self.assertIn("--head learn/fix-a-thing", log)
        self.assertIn("@coderabbitai review", log)

    def test_contributor_pushes_to_their_own_fork(self):
        fork = self.hub / "alice" / "mixing-console-skills.git"
        fork.parent.mkdir()
        git(self.hub, "clone", "-q", "--bare", str(self.upstream), str(fork))
        bob = self.hub / "bob" / "mixing-console-skills.git"
        bob.parent.mkdir()
        git(self.hub, "clone", "-q", "--bare", str(self.upstream), str(bob))
        git(self.clone, "remote", "add", "fork", "https://github.com/bob/mixing-console-skills.git")
        (self.skill / "SKILL.md").write_text("skill v2\n")
        r = self.run_script(login="alice")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("learn/fix-a-thing", git(fork, "branch", "--list"))
        self.assertNotIn("learn/fix-a-thing", git(bob, "branch", "--list"))
        self.assertIn("--head alice:learn/fix-a-thing", self.log.read_text())

    def test_unpushed_commit_in_a_single_branch_clone_is_refused(self):
        git(self.upstream, "branch", "dev", "main")
        single = Path(self.tmp.name) / "single"
        git(self.tmp.name, "clone", "-q", "--single-branch", "--branch", "dev",
            "https://github.com/DominikKriss/mixing-console-skills.git", str(single))
        (single / "README.md").write_text("local\n")
        git(single, "commit", "-qam", "local")
        (single / "lv1-session" / "SKILL.md").write_text("skill v2\n")
        r = subprocess.run(["bash", str(single / "lv1-session" / "scripts" / "contribute.sh"), "--title", "t",
                            "--body-file", str(self.body), "--dry-run"], env=self.env, capture_output=True, text=True)
        self.assertEqual(r.returncode, 4, r.stdout + r.stderr)
    def test_chosen_email_wins_over_git_identity_variables(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        r = self.run_script("--email", "1+me@users.noreply.github.com", GIT_AUTHOR_EMAIL="private@example.com",
                            GIT_COMMITTER_EMAIL="private@example.com")
        self.assertEqual(r.returncode, 0, r.stderr)
        log = git(self.upstream, "log", "-1", "--format=%ae %ce", "learn/fix-a-thing")
        self.assertEqual(log.split(), ["1+me@users.noreply.github.com"] * 2)

    def test_resume_after_the_pr_could_not_be_opened(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        first = self.run_script(FAKE_GH_FAIL_PR="1")
        self.assertEqual(first.returncode, 5, first.stdout + first.stderr)
        commits = git(self.clone, "rev-list", "--count", "HEAD")
        again = self.run_script()
        self.assertEqual(again.returncode, 0, again.stdout + again.stderr)
        self.assertIn("resuming", again.stdout)
        self.assertEqual(git(self.clone, "rev-list", "--count", "HEAD"), commits)
        self.assertEqual(self.log.read_text().count("pr create"), 2)

    def test_resume_when_the_pr_is_already_open(self):
        (self.skill / "SKILL.md").write_text("skill v2\n")
        self.run_script(FAKE_GH_FAIL_PR="1")
        r = self.run_script(FAKE_GH_PR_OPEN="1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn("already open", r.stdout)

    def test_learn_branch_with_other_files_is_not_resumed(self):
        git(self.clone, "checkout", "-q", "-b", "learn/x")
        (self.clone / "README.md").write_text("local\n")
        git(self.clone, "commit", "-qam", "local")
        self.assertEqual(self.run_script("--dry-run").returncode, 1)

if __name__ == "__main__":
    unittest.main()
