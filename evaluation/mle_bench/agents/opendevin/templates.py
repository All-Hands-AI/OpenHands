from string import Template

config_template = Template(
    """
[core]
workspace_base="${workspace_base}"
workspace_mount_path="${workspace_base}"
workspace_mount_path_in_sandbox="${workspace_mount_path_in_sandbox}"
default_agent="${agent}"
max_iterations=${max_steps}
persist_sandbox=false

[llm]
model="${model}"
api_key="${api_key}"
embedding_model=""

[sandbox]
user_id=1000
use_host_network=true
timeout=86400
shm_size="${shm_size}"
"""
)

additional_notes_template = Template(
    """
ADDITIONAL NOTES
------
- **Compute**: You have access to a ${type_of_processor} with the appropriate drivers installed.
- **Total Runtime**: You have a maximum of ${max_time_in_hours} hours to attempt this task. You may iteratively develop your solution within this time frame, but bear in mind that program runtime also counts towards this limit.
- **Total Steps**: You have a maximum of ${max_steps} steps to submit your solution.
- You only have read and write permissions to the files that you create. You therefore cannot use the helper script `/home/validate_submission.sh`. Instead, use the HTTP endpoint (e.g. via `curl -X POST -F "file=@/path/to/your/file" http://localhost:5000/validate`) to validate your submission.
- You must write all of the code necessary to produce the `submission.csv` in `${workspace}`. You must not write to any other location.
- You must use all the time available to you, unless you've achieved the maximum possible score for the competition. Do not stop until you've reached the maximum possible score.
"""
)
