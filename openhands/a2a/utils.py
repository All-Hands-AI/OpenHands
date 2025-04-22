import yaml

from openhands.a2a.common.types import Part


def convert_parts(parts: list[Part]) -> list[str]:
    rval = []
    for p in parts:
        rval.append(convert_part(p))
    return rval


def convert_part(part: Part):
    if part.type == 'text':
        return part.text
    elif part.type == 'data':
        # Convert data dictionary to YAML format for better readability
        try:
            # Add a header and use explicit_start=True for better YAML formatting
            yaml_header = (
                '# Data content converted to YAML format for better readability\n'
            )
            yaml_content = yaml.dump(
                part.data,
                default_flow_style=False,
                sort_keys=False,
                explicit_start=True,
                width=80,
            )
            return yaml_header + yaml_content
        except Exception as e:
            # Fallback to original data if YAML conversion fails
            return f'Error converting to YAML: {str(e)}\nOriginal data: {part.data}'
    #   elif part.type == "file":
    #     # Repackage A2A FilePart to google.genai Blob
    #     # Currently not considering plain text as files
    #     file_id = part.file.name
    #     file_bytes = base64.b64decode(part.file.bytes)
    #     file_part = types.Part(
    #       inline_data=types.Blob(
    #         mime_type=part.file.mimeType,
    #         data=file_bytes))
    #     tool_context.save_artifact(file_id, file_part)
    #     tool_context.actions.skip_summarization = True
    #     tool_context.actions.escalate = True
    #     return DataPart(data = {"artifact-file-id": file_id})
    else:
        return f'Unknown type: {part.type}'
