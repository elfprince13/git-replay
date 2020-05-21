# git-replay
Implements a pseudo-`git rebase` for correcting author info in a branch (including merges), in terms of alternating `git cherry-pick` and `git commit --amend`.

Doesn't handle everything (I've observed difficulties if `git-lfs` data is somehow in an inconsistent state), but saves a lot of effort compared to just using `git rebase`.

Pull requests happily accepted.
