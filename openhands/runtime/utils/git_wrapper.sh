#!/bin/bash

# Git wrapper script that automatically adds co-authorship to commit messages
# This script intercepts git commit commands and adds "Co-authored-by: openhands <openhands@all-hands.dev>"
# if it's not already present in the commit message.

# Function to add co-authorship to a commit message
add_coauthorship() {
    local commit_msg_file="$1"
    local coauthor_line="Co-authored-by: openhands <openhands@all-hands.dev>"

    # Check if co-authorship line already exists (case-insensitive)
    if ! grep -qi "co-authored-by.*openhands" "$commit_msg_file" 2>/dev/null; then
        # Add two empty lines and the co-authorship line
        echo "" >> "$commit_msg_file"
        echo "" >> "$commit_msg_file"
        echo "$coauthor_line" >> "$commit_msg_file"
    fi
}

# Function to handle git commit with message
handle_commit_with_message() {
    local temp_msg_file
    temp_msg_file=$(mktemp)

    # Extract the commit message from arguments
    local commit_msg=""
    local args=()
    local skip_next=false

    for arg in "$@"; do
        if [ "$skip_next" = true ]; then
            commit_msg="$arg"
            args+=("$arg")
            skip_next=false
        elif [ "$arg" = "-m" ] || [ "$arg" = "--message" ]; then
            args+=("$arg")
            skip_next=true
        else
            args+=("$arg")
        fi
    done

    # Write the commit message to temp file and add co-authorship
    echo "$commit_msg" > "$temp_msg_file"
    add_coauthorship "$temp_msg_file"

    # Replace -m argument with -F (file) argument
    local new_args=()
    skip_next=false
    for arg in "${args[@]}"; do
        if [ "$skip_next" = true ]; then
            new_args+=("-F" "$temp_msg_file")
            skip_next=false
        elif [ "$arg" = "-m" ] || [ "$arg" = "--message" ]; then
            skip_next=true
        else
            new_args+=("$arg")
        fi
    done

    # Execute git with modified arguments
    command git "${new_args[@]}"
    local exit_code=$?

    # Clean up temp file
    rm -f "$temp_msg_file"

    return $exit_code
}

# Main logic
if [ "$1" = "commit" ]; then
    # Check if this is a commit with -m/--message flag
    if [[ "$*" =~ -m[[:space:]] ]] || [[ "$*" =~ --message[[:space:]] ]] || [[ "$*" =~ -m= ]] || [[ "$*" =~ --message= ]]; then
        handle_commit_with_message "$@"
    else
        # For other commit types (interactive, -F file, etc.), just pass through
        # The prepare-commit-msg hook would handle these in Docker runtime
        command git "$@"
    fi
else
    # For non-commit commands, just pass through to real git
    command git "$@"
fi
