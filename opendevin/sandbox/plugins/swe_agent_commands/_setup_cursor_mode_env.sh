# Cursor Mode from SWE-Bench
# https://github.com/princeton-nlp/SWE-agent/blob/ca54d5556b9db4f4f2be21f09530ce69a72c0305/config/configs/default_sys-env_cursors_window100-detailed_cmd_format-last_5_history-1_demos.yaml
export WINDOW=200;
export OVERLAP=2;
export CURRENT_LINE=0;
export CURRENT_FILE='';
export SEARCH_RESULTS=();
export SEARCH_FILES=();
export SEARCH_INDEX=0;
export START_INDEX=0;
export END_INDEX=0;
export START_CURSOR=0;
export END_CURSOR=0;
export START_CURSOR_MARK='"<<<<< START CURSOR >>>>>"';  # these have to use double quotes
export END_CURSOR_MARK='"<<<<< END CURSOR >>>>>"'; # these have to use double quotes

state() {
    local working_dir="$PWD";
    if [ -z $CURRENT_FILE ]; then
        echo '{"open_file": "n/a", "working_dir": "'$working_dir'"}';
    else
        echo '{"open_file": "'$(realpath $CURRENT_FILE)'", "working_dir": "'$working_dir'"}';
    fi
};
