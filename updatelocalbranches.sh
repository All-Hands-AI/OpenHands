git fetch -p && git branch -vv | grep ': gone]' | awk '{print $1}' | while read branch; do echo "Deleting local branch: $branch"; git branch -D $branch; done
