# Plan: history rewrite before pushing (NOT executed)

Status: planned only. Nothing in this plan has been run. Executing it needs the owner's explicit go-ahead, because it ends in a force-push to the default branch.

## What is actually exposed (measured with `git log -S` / `git grep`)

| Item | Where | Public? |
|---|---|---|
| A Windows user-profile path (`C:\Users\<name>\Downloads\<repo folder>`) in an old README line | commit `337d95a` and the README at the tip of `origin/master` | **Yes**, already on GitHub. Only 2 public commits come after it. `origin/improve/pi5-slam-benchmark` does not contain it. |
| The same path, transient | local commits `435e065` (removes it), `61a86de` (my report quoted it), `ae0998f` (removed again) | No, local only. No extra exposure: it is the same string already public. |
| Google Drive file id | nowhere in any commit | n/a |
| Contributors' e-mail addresses (two personal Gmail addresses, one placeholder `your@email.com`) | author/committer metadata of existing public commits | Yes, already public as commit metadata |

The path contains the generic Windows account name `user` and a folder name. Sensitivity is low.

## Options

| | A. Leave history as is (recommended default) | B. Targeted rewrite of the path only | C. Fresh repository |
|---|---|---|---|
| What changes | Nothing. Merging this branch removes the line from the tip; history keeps it. | Replace the path string in 1 public commit and its 2 descendants, plus my 8 local commits. | New repo, squashed history. |
| Public hashes affected | 0 | 3 public commits (`337d95a` and the two after it) | all |
| Needs force-push | no | **yes** (`master`) | n/a |
| Collaborators | none affected | anyone with a clone or open PR must re-clone or rebase | all lose history and credit |
| Removes the string from GitHub | no | from the branch history only; old commits stay reachable by hash, in forks and in caches until GitHub garbage-collects (a support request can speed this up; no guarantee) | from this repo only |
| Verdict | acceptable given low sensitivity | worth it only if you want the string gone from the branch history | not recommended: loses contributor attribution |

E-mail addresses: do **not** rewrite. They are the contributors' own public commit identities; rewriting changes their attribution and needs their consent. If you want them hidden in display, a `.mailmap` file changes how tools show them without altering history.

## Steps for option B (if you choose it)

1. **Back up** outside the working folder: `git clone --mirror <repo> <backup>.git` and `git bundle create <backup>.bundle --all`.
2. **Work on a fresh mirror clone**, never in the working repo.
3. Install the tool in user scope: `pip install git-filter-repo` (a new dev-time dependency, justified only for this task).
4. Create `replacements.txt` with one rule: the literal path => `<local path>`.
5. Run `git filter-repo --replace-text replacements.txt` in the clone (rewrites all branches).
6. **Verify before anything leaves the machine:**
   - `git log --all -S "<path fragment>"` returns nothing;
   - `git diff <old-tip> <new-tip> --stat` shows only the one README line changed;
   - the unit tests pass on the rewritten tip (`python -B -m unittest discover -s tests`);
   - the branch `refine/autonav-lab` still sits on top of the rewritten `master`.
7. **Owner-approved push** (the only irreversible step): `git push --force-with-lease origin master`, then push the feature branch. Check for branch protection first.
8. Tell collaborators (Priyangshu Ghosh, Sreyas24) to re-clone or `git fetch && git rebase`. Close or re-open any PR opened against the old hashes.
9. Optionally ask GitHub Support to purge cached views of the old commits.

## Effort and risk
About 15 minutes of work. Risk is in step 7 (force-push to the default branch; collaborators' clones diverge). Steps 1-6 are fully reversible.

## Decision needed from the owner
Choose A or B. If B: confirm that force-pushing `master` is acceptable and that the two collaborators will be told.