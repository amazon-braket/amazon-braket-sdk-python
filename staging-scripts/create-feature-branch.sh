# run like ./create-feature-branch.sh <feature-name> to create a new branch feature/<feature-name>
# locally and in the staging repo

FEATURE_NAME=$1

git checkout main
git rebase public/main
git checkout -b feature/"$FEATURE_NAME"
git push staging feature/"$FEATURE_NAME"

echo "Feature branch created: https://github.com/aws/amazon-braket-default-simulator-python/tree/feature/$FEATURE_NAME"
echo "Start developing by branching off of and creating PRs into feature/$FEATURE_NAME"
