# run from a branch when you're ready to publish that branch to the public repo

BRANCH_NAME=$(git branch --show-current)

TAG_NAME="STAGING_SETUP"

git checkout -b "$BRANCH_NAME"-copy
git reset --hard "$TAG_NAME"~
git checkout "$BRANCH_NAME"
git checkout -b "$BRANCH_NAME"-published
git rebase --onto "$BRANCH_NAME"-copy "$TAG_NAME"
git branch -D "$BRANCH_NAME"-copy

git push staging "$BRANCH_NAME"-published


echo ""
echo "Created a dry-run PR in the staging repo. Run the repo-sync workflow to update public-main
and set the base branch to public-main to make sure the PR looks good. Once you're ready, delete the
unpublished version, rename the published version, and push this branch to the public repo."
