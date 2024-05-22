# @yaml
# signature: |-
#   edit <<EOF
#   <replacement_text>
#   EOF
# docstring: replaces *all* of the text between the START CURSOR and the END CURSOR with the replacement_text. The replacement text is delineated using heredoc syntax. All of the <replacement_text> will be entered, so make sure your indentation is formatted properly. To enter text at the beginning of the file, set START CURSOR and END CURSOR to 0. Use set_cursors to move the cursors around. Python files will be checked for syntax errors after the edit.
# arguments:
#   replacement_text:
#     type: string
#     description: the text to replace the current selection with
#     required: true
edit() {
    if [ -z "$CURRENT_FILE" ]
    then
        echo 'No file is opened. Use the `open` command first.'
        return
    fi
    local start_line=$((START_CURSOR - 1))
    start_line=$((start_line < 0 ? 0 : start_line))
    local end_line=$((END_CURSOR))
    end_line=$((end_line < 0 ? 0 : end_line))

    local replacement=()
    while IFS= read -r line
    do
        replacement+=("$line")
    done

    local num_lines=${#replacement[@]}
    # Create a backup of the current file
    cp "$CURRENT_FILE" "$SWE_CMD_WORK_DIR/$(basename "$CURRENT_FILE")_backup"
    # Read the file line by line into an array
    mapfile -t lines < "$CURRENT_FILE"
    local new_lines=("${lines[@]:0:$start_line}" "${replacement[@]}" "${lines[@]:$((end_line))}")
    # Write the new stuff directly back into the original file
    printf "%s\n" "${new_lines[@]}" >| "$CURRENT_FILE"
    # Run linter if enabled
    if [[ $CURRENT_FILE == *.py && -n "$ENABLE_AUTO_LINT" ]]; then
        lint_output=$(flake8 --isolated --select=F821,F822,F831,E111,E112,E113,E999,E902 "$CURRENT_FILE" 2>&1)
    else
        # do nothing
        lint_output=""
    fi
    # if there is no output, then the file is good
    if [ -z "$lint_output" ]; then
        _constrain_line
        # set to START + num_lines - 1, unless num_lines is 0, then set to START
        export END_CURSOR=$((num_lines == 0 ? START_CURSOR : START_CURSOR + num_lines - 1))
        export START_CURSOR=$START_CURSOR
        _print
        echo "File updated. Please review the changes and make sure they are correct (correct indentation, no duplicate lines, etc). Edit the file again if necessary."
    else
        echo "Your proposed edit has introduced new syntax error(s). Please understand the fixes and retry your edit command."
        echo ""
        echo "ERRORS:"
        _split_string "$lint_output"
        echo ""

        # Save original values
        original_current_line=$CURRENT_LINE
        original_window=$WINDOW
        original_end_cursor=$END_CURSOR

        # Update values
        export CURRENT_LINE=$(( (num_lines / 2) + start_line )) # Set to "center" of edit
        export WINDOW=$((num_lines + 10)) # Show +/- 5 lines around edit
        export END_CURSOR=$((num_lines == 0 ? START_CURSOR : START_CURSOR + num_lines - 1))

        echo "This is how your edit would have looked if applied"
        echo "-------------------------------------------------"
        _constrain_line
        _print
        echo "-------------------------------------------------"
        echo ""

        # Restoring CURRENT_FILE to original contents.
        cp "$SWE_CMD_WORK_DIR/$(basename "$CURRENT_FILE")_backup" "$CURRENT_FILE"

        export CURRENT_LINE=$(( ((end_line - start_line) / 2) + start_line )) # Set to "center" of edit
        export WINDOW=$((end_line - start_line + 10))
        export END_CURSOR=$original_end_cursor

        echo "This is the original code before your edit"
        echo "-------------------------------------------------"
        _constrain_line
        _print
        echo "-------------------------------------------------"

        # Restore original values
        export CURRENT_LINE=$original_current_line
        export WINDOW=$original_window
        export END_CURSOR=$original_end_cursor

        echo "Your changes have NOT been applied. Please fix your edit command and try again."
        echo "You either need to 1) Specify the correct start/end line arguments or 2) Correct your edit code."
        echo "DO NOT re-run the same failed edit command. Running it again will lead to the same error."
    fi
    # Remove backup file
    rm -f "$SWE_CMD_WORK_DIR/$(basename "$CURRENT_FILE")_backup"
}
