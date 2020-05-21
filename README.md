# git-replay
Implements a pseudo-`git rebase` for correcting author info in a branch (including merges), in terms of alternating `git cherry-pick` and `git commit --amend`.

Doesn't handle everything (I've observed difficulties if `git-lfs` data is somehow in an inconsistent state), but saves a lot of effort compared to just using `git rebase`.

# Usage
From the working directory of your repo:
```bash
git-replay.py "Bad User" "bad@email" "Good User" "good@email" master src-branch dst-branch
```
Will replace `Bad User <bad@email>` with `Good User <good@email>` (for both author and committer) in every commit of `src-branch` that does not appear in `master` (as determined by `git log master..src-branch`) by cherry-picking into `dst-branch` and then amending the result. `dst-branch` will be created, as the script runs, and must therefore not already exist.

Note that neither `Bad User <other@email>` nor `Other User <bad@email>` will be replaced.

# Recovery

```bash
git cherry-pick --abort
git checkout src-branch
git branch -D dst-branch
```

# Misc.
Pull requests happily accepted.

