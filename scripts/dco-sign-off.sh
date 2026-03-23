#!/usr/bin/env bash
# Adds a DCO Signed-off-by line to commit messages if not already present.

COMMIT_MSG_FILE="$1"

if ! grep -q "^Signed-off-by: " "$COMMIT_MSG_FILE"; then
    SOB=$(git var GIT_COMMITTER_IDENT | sed -n 's/^\(.*>\).*/Signed-off-by: \1/p')
    echo "" >> "$COMMIT_MSG_FILE"
    echo "$SOB" >> "$COMMIT_MSG_FILE"
fi
