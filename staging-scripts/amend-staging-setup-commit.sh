# use this script to commit changes to the staging setup commit while preserving the tag

git commit --amend --no-edit
git tag --delete STAGING_SETUP
git tag -a STAGING_SETUP -m "STAGING_SETUP"
