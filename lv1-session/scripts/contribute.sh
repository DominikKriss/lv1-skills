#!/usr/bin/env bash
# Opens a pull request to the lv1-skills repo with the changes made to this skill folder,
# from the GitHub account that is active in `gh`. Run with --dry-run first and show the output to the user.
set -euo pipefail

UPSTREAM="DominikKriss/lv1-skills"
usage() {
  cat <<EOF
usage: contribute.sh --title "<PR title>" --body-file <file> [--branch <name>] [--email <commit email>] [--dry-run]
EOF
  exit 2
}

TITLE="" BODY="" BRANCH="" EMAIL="" DRY=0
while [ $# -gt 0 ]; do
  case "$1" in
    --title) TITLE="$2"; shift 2 ;;
    --body-file) BODY="$2"; shift 2 ;;
    --branch) BRANCH="$2"; shift 2 ;;
    --email) EMAIL="$2"; shift 2 ;;
    --dry-run) DRY=1; shift ;;
    *) usage ;;
  esac
done
[ -n "$TITLE" ] && [ -n "$BODY" ] || usage
[ -f "$BODY" ] || { echo "body file not found: $BODY" >&2; exit 2; }
BODY="$(cd "$(dirname "$BODY")" && pwd -P)/$(basename "$BODY")"

command -v gh >/dev/null || { echo "gh (GitHub CLI) is not installed: https://cli.github.com" >&2; exit 3; }
LOGIN="$(gh api user -q .login 2>/dev/null)" || { echo "gh is not logged in: run 'gh auth login'" >&2; exit 3; }

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
SKILL_NAME="$(basename "$SKILL_DIR")"

# An install that is a clone of the repo is used as is; a plain copy is diffed against a fresh clone.
REPO=""
if top="$(git -C "$SKILL_DIR" rev-parse --show-toplevel 2>/dev/null)" \
   && git -C "$top" remote get-url origin 2>/dev/null | grep -qi "$UPSTREAM"; then
  REPO="$top"
  REL="$(python3 -c 'import os,sys; print(os.path.relpath(sys.argv[1], sys.argv[2]))' "$SKILL_DIR" "$REPO")"
else
  TMP="$(mktemp -d)"
  trap 'rm -rf "$TMP"' EXIT
  git clone -q "https://github.com/$UPSTREAM.git" "$TMP/repo"
  REPO="$TMP/repo"
  REL="$SKILL_NAME"
  [ -d "$REPO/$REL" ] || { echo "upstream has no folder $REL" >&2; exit 3; }
  rsync -a --delete --exclude '__pycache__' --exclude '.DS_Store' "$SKILL_DIR/" "$REPO/$REL/"
  echo "note: this install is not a git clone; changes are compared with upstream main, so anything upstream added since you copied the skill shows as removed."
fi

cd "$REPO"
CHANGED="$(git status --porcelain -- "$REL")"
[ -n "$CHANGED" ] || { echo "no changes in $REL"; exit 1; }
if git status --porcelain -z --untracked-files=all -- "$REL" | tr '\0' '\n' | grep -Eiq '\.(emo|scn|dat)$|__pycache__'; then
  echo "refusing: session / scene files are among the changes; keep them out of the skill folder" >&2
  exit 4
fi
OUTSIDE="$(git diff --cached --name-only -- . ":(exclude)$REL")"
if [ -n "$OUTSIDE" ]; then
  echo "refusing: files outside $REL are staged and would be committed too; unstage them first:" >&2
  echo "$OUTSIDE" >&2
  exit 4
fi
git fetch -q origin refs/heads/main
UPSTREAM_MAIN="$(git rev-parse FETCH_HEAD)"
AHEAD="$(git rev-list "$UPSTREAM_MAIN..HEAD")"
if [ -n "$AHEAD" ]; then
  echo "refusing: this branch has commits that aren't on upstream main; they would be published with the PR:" >&2
  git log --oneline "$UPSTREAM_MAIN..HEAD" >&2
  exit 4
fi

AUTHOR_EMAIL="${EMAIL:-$(git config user.email || true)}"
AUTHOR_NAME="$(git config user.name || echo "$LOGIN")"
[ -n "$BRANCH" ] || BRANCH="learn/$(echo "$TITLE" | tr '[:upper:]' '[:lower:]' | tr -cs 'a-z0-9' '-' | sed 's/^-//; s/-$//' | cut -c1-40)"

if [ "$LOGIN" = "${UPSTREAM%%/*}" ]; then PUSH_TO="origin (maintainer)"; HEAD="$BRANCH"
else PUSH_TO="fork $LOGIN/${UPSTREAM##*/}"; HEAD="$LOGIN:$BRANCH"; fi

echo "GitHub account : $LOGIN"
echo "commit author  : $AUTHOR_NAME <$AUTHOR_EMAIL>"
echo "branch         : $BRANCH -> $PUSH_TO"
echo "pull request   : $UPSTREAM  \"$TITLE\""
echo "files:"
git status --porcelain --untracked-files=all -- "$REL" | sed 's/^/  /'
git --no-pager diff --stat -- "$REL"
if [ "$DRY" = 1 ]; then echo "dry run: nothing committed or pushed"; exit 0; fi

git checkout -q -b "$BRANCH"
git add -- "$REL"
git -c user.email="$AUTHOR_EMAIL" -c user.name="$AUTHOR_NAME" commit -q -m "$TITLE"

if [ "$LOGIN" = "${UPSTREAM%%/*}" ]; then
  git push -q -u origin "$BRANCH"
else
  gh repo fork "$UPSTREAM" --clone=false >/dev/null 2>&1 || true
  FORK_URL="https://github.com/$LOGIN/${UPSTREAM##*/}.git"
  pushed=0
  for _ in 1 2 3 4 5; do
    if git push -q "$FORK_URL" "$BRANCH"; then pushed=1; break; fi
    sleep 3
  done
  [ "$pushed" = 1 ] || { echo "push to $FORK_URL failed; the commit is on local branch $BRANCH" >&2; exit 5; }
fi

PR_URL="$(gh pr create --repo "$UPSTREAM" --base main --head "$HEAD" --title "$TITLE" --body-file "$BODY")"
echo "$PR_URL"
# CodeRabbit reviews repos under 10 stars only on request.
gh pr comment "$PR_URL" --body "@coderabbitai review" >/dev/null || echo "note: couldn't request the CodeRabbit review; comment '@coderabbitai review' on the PR"
