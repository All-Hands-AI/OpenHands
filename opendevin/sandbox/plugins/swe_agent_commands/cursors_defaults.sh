_reset_cursors() {
    export START_CURSOR=1
    export END_CURSOR=1
}

_constrain_cursors() {
    # constrain the cursors to be within the bounds of the file [0, total_lines+1]
    local total_lines=$(awk 'END {print NR}' "$CURRENT_FILE")
    total_lines=$((total_lines < 1 ? 1 : total_lines))  # if the file is empty, set total_lines to 1
    local start_line=$((CURRENT_LINE - WINDOW / 2))
    local end_line=$((CURRENT_LINE + WINDOW / 2))
    start_line=$((start_line < 1 ? 1 : start_line))
    end_line=$((end_line > total_lines ? total_lines : end_line))
    local warning_string=""
    if [ "$START_CURSOR" -lt "$start_line" ]; then
        warning_string+="START_CURSOR moved to $start_line\n"
        START_CURSOR=$start_line
    elif [ "$START_CURSOR" -gt "$end_line" ]; then
        START_CURSOR=$end_line
        warning_string+="START_CURSOR moved to $end_line\n"
    fi
    if [ "$END_CURSOR" -lt "$start_line" ]; then
        warning_string+="END_CURSOR moved to $start_line\n"
        END_CURSOR=$start_line
    elif [ "$END_CURSOR" -gt "$end_line" ]; then
        warning_string+="END_CURSOR moved to $end_line\n"
        END_CURSOR=$end_line
    fi
    export START_CURSOR END_CURSOR
    echo "$warning_string"
    echo $START_CURSOR $END_CURSOR
}

_print() {
    local cursor_warning=$(_constrain_cursors)
    local cursor_values=$(echo "$cursor_warning" | tail -n 1)
    cursor_warning=$(echo "$cursor_warning" | head -n -1)
    export START_CURSOR=$(echo "$cursor_values" | awk '{print $1}')
    export END_CURSOR=$(echo "$cursor_values" | awk '{print $2}')
    local total_lines=$(awk 'END {print NR}' $CURRENT_FILE)
    echo "[File: $(realpath "$CURRENT_FILE") ($total_lines lines total)]"
    local start_line=$((CURRENT_LINE - WINDOW / 2))
    local end_line=$((CURRENT_LINE + WINDOW / 2))
    start_line=$((start_line < 1 ? 1 : start_line))
    end_line=$((end_line > total_lines ? total_lines : end_line))
    local lines=()
    local i=0
    while IFS= read -r line; do
        lines[i++]="$line"
    done < <(awk -v start="$start_line" -v end="$end_line" 'NR>=start && NR<=end {print}' "$CURRENT_FILE")
    local num_lines=${#lines[@]}
    if [ $start_line -gt 1 ]; then
        echo "($((start_line - 1)) more lines above)"
    fi
    for ((i=0; i<num_lines+1; i++)) do
        local line_number=$((start_line + i))
        if [ $line_number -eq $START_CURSOR ]
        then
            echo $START_CURSOR_MARK
        fi
        # if i in [0, num_lines-1] then print the line number and the line
        if [ $i -ge 0 ] && [ $i -lt $num_lines ]
        then
            echo "$line_number:${lines[i]}"
        fi
        if [ $line_number -eq $END_CURSOR ]
        then
            echo $END_CURSOR_MARK
        fi
    done
    lines_below=$(jq -n "$total_lines - $start_line - $num_lines" | jq '[0, .] | max')
    if [ $lines_below -gt 0 ]; then
        echo "($lines_below more lines below)"
    fi
    if [ -n "$cursor_warning" ]; then
        echo -e "$cursor_warning"
    fi
}

_constrain_line() {
    if [ -z "$CURRENT_FILE" ]
    then
        echo "No file open. Use the open command first."
        return
    fi
    local max_line=$(awk 'END {print NR}' $CURRENT_FILE)
    local half_window=$(jq -n "$WINDOW/2" | jq 'floor')
    export CURRENT_LINE=$(jq -n "[$CURRENT_LINE, $max_line - $half_window] | min")
    export CURRENT_LINE=$(jq -n "[$CURRENT_LINE, $half_window] | max")
}

# @yaml
# signature: set_cursors <start_line> <end_line>
# docstring: sets the start and end cursors to the given line numbers
# arguments:
#   start_line:
#     type: integer
#     description: the line number to set the start cursor to
#     required: true
#   end_line:
#     type: integer
#     description: the line number to set the end cursor to
#     required: true
set_cursors() {
    if [ -z "$CURRENT_FILE" ]
    then
        echo "No file open. Use the open command first."
        return
    fi
    if [ $# -lt 2 ]
    then
        echo "Usage: set_cursors <start_line> <end_line>"
        return
    fi
    local start_line=$1
    local end_line=$2
    local re='^[0-9]+$'
    if ! [[ $start_line =~ $re ]]
    then
        echo "Usage: set_cursors <start_line> <end_line>"
        echo "Error: start_line must be a number"
        return
    fi
    if ! [[ $end_line =~ $re ]]
    then
        echo "Usage: set_cursors <start_line> <end_line>"
        echo "Error: end_line must be a number"
        return
    fi
    if [ $start_line -gt $end_line ]
    then
        echo "Usage: set_cursors <start_line> <end_line>"
        echo "Error: start_line must be less than or equal to end_line"
        return
    fi
    export START_CURSOR=$start_line
    export END_CURSOR=$end_line
    _print
}

# @yaml
# signature: open <path> [<line_number>]
# docstring: opens the file at the given path in the editor. If line_number is provided, the window will be centered on that line
# arguments:
#   path:
#     type: string
#     description: the path to the file to open
#     required: true
#   line_number:
#     type: integer
#     description: the line number to move the window to (if not provided, the window will start at the top of the file)
#     required: false
open() {
    if [ -z "$1" ]
    then
        echo "Usage: open <file>"
        return
    fi
    # Check if the second argument is provided
    if [ -n "$2" ]; then
        # Check if the provided argument is a valid number
        if ! [[ $2 =~ ^[0-9]+$ ]]; then
            echo "Usage: open <file> [<line_number>]"
            echo "Error: <line_number> must be a number"
            return  # Exit if the line number is not valid
        fi
        local max_line=$(awk 'END {print NR}' $1)
        if [ $2 -gt $max_line ]; then
            echo "Warning: <line_number> ($2) is greater than the number of lines in the file ($max_line)"
            echo "Warning: Setting <line_number> to $max_line"
            local line_number=$(jq -n "$max_line")  # Set line number to max if greater than max
        elif [ $2 -lt 1 ]; then
            echo "Warning: <line_number> ($2) is less than 1"
            echo "Warning: Setting <line_number> to 1"
            local line_number=$(jq -n "1")  # Set line number to 1 if less than 1
        else
            local line_number=$(jq -n "$2")  # Set line number if valid
        fi
    else
        local line_number=$(jq -n "$WINDOW/2")  # Set default line number if not provided
    fi

    if [ -f "$1" ]; then
        export CURRENT_FILE=$(realpath $1)
        export CURRENT_LINE=$line_number
        _constrain_line
        _print
    else
        echo "File $1 not found"
    fi
}

# @yaml
# signature: scroll_down
# docstring: moves the window down {WINDOW} lines
scroll_down() {
    if [ -z "$CURRENT_FILE" ]
    then
        echo "No file open. Use the open command first."
        return
    fi
    export CURRENT_LINE=$(jq -n "$CURRENT_LINE + $WINDOW - $OVERLAP")
    _constrain_line
    _print
}

# @yaml
# signature: scroll_up
# docstring: moves the window up {WINDOW} lines
scroll_up() {
    if [ -z "$CURRENT_FILE" ]
    then
        echo "No file open. Use the open command first."
        return
    fi
    export CURRENT_LINE=$(jq -n "$CURRENT_LINE - $WINDOW + $OVERLAP")
    _constrain_line
    _print
}

# @yaml
# signature: goto <line_number>
# docstring: moves the window to show <line_number>
# arguments:
#   line_number:
#     type: integer
#     description: the line number to move the window to
#     required: true
goto() {
    if [ $# -gt 1 ]; then
        echo "goto allows only one line number at a time."
        return
    fi
    if [ -z "$CURRENT_FILE" ]
    then
        echo "No file open. Use the open command first."
        return
    fi
    if [ -z "$1" ]
    then
        echo "Usage: goto <line>"
        return
    fi
    if ! [[ $1 =~ ^[0-9]+$ ]]
    then
        echo "Usage: goto <line>"
        echo "Error: <line> must be a number"
        return
    fi
    local max_line=$(awk 'END {print NR}' $CURRENT_FILE)
    if [ $1 -gt $max_line ]
    then
        echo "Error: <line> must be less than or equal to $max_line"
        return
    fi
    local OFFSET=$(jq -n "$WINDOW/6" | jq 'floor')
    export CURRENT_LINE=$(jq -n "[$1 + $WINDOW/2 - $OFFSET, 1] | max | floor")
    _constrain_line
    _print
}

# @yaml
# signature: create <filename>
# docstring: creates and opens a new file with the given name
# arguments:
#   filename:
#     type: string
#     description: the name of the file to create
#     required: true
create() {
    if [ -z "$1" ]; then
        echo "Usage: create <filename>"
        return
    fi

    # Check if the file already exists
    if [ -e "$1" ]; then
        echo "Error: File '$1' already exists."
		open "$1"
        return
    fi

    # Create the file an empty new line
    printf "\n" > "$1"
    # Use the existing open command to open the created file
    open "$1"
}

# @yaml
# signature: submit
# docstring: submits your current code and terminates the session
submit() {
    cd $ROOT

    # Check if the patch file exists and is non-empty
    if [ -s "$SWE_CMD_WORK_DIR/test.patch" ]; then
        # Apply the patch in reverse
        git apply -R < "$SWE_CMD_WORK_DIR/test.patch"
    fi

    git add -A
    git diff --cached > model.patch
    echo "<<SUBMISSION||"
    cat model.patch
    echo "||SUBMISSION>>"
}
