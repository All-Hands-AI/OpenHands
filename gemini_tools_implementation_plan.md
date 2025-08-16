# Gemini-Optimized Tools Implementation Plan

## Overview

This document outlines the plan to implement Gemini-optimized file editing tools for OpenHands, inspired by the excellent design patterns found in Google's Gemini-CLI project.

## Current State Analysis

### OpenHands CodeActAgent Tools
- **str_replace_editor**: Uses exact string matching with `old_str`/`new_str` parameters
- **Limitations**:
  - Requires very precise matching (whitespace, indentation)
  - No built-in error correction
  - Fails if string appears multiple times or doesn't match exactly
  - Not optimized for Gemini's capabilities

### Gemini-CLI Tools (Superior Design)
- **replace tool**: Uses `old_string`/`new_string` with smart correction
- **write_file tool**: Writes entire file content with validation
- **read_file tool**: Reads files with offset/limit support
- **Key advantages**:
  - Uses Gemini itself for content correction via `ensureCorrectEdit`
  - Better error handling and user feedback
  - IDE integration for diff previews
  - Automatic content validation and correction
  - More forgiving of minor formatting differences

### openhands-aci
- Provides the runtime execution environment inside Docker containers
- Has OHEditor class for file operations
- Needs to be extended to support new Gemini-optimized tools

## Implementation Plan

### Phase 1: Core Tool Implementation in openhands-aci

#### 1.1 Create Gemini-Optimized Editor Tools
**Location**: `openhands-aci/openhands_aci/editor/gemini_tools.py`

Implement three core tools mirroring Gemini-CLI's approach:

1. **GeminiReplaceEditor**
   - Similar to Gemini-CLI's `replace` tool
   - Uses LLM-assisted content correction
   - Parameters: `file_path`, `old_string`, `new_string`, `expected_replacements`
   - Smart error recovery and suggestions

2. **GeminiWriteFileEditor**
   - Similar to Gemini-CLI's `write_file` tool
   - Writes entire file content with validation
   - Parameters: `file_path`, `content`
   - Content validation and correction

3. **GeminiReadFileEditor**
   - Enhanced file reading with range support
   - Parameters: `absolute_path`, `offset`, `limit`
   - Better error messages and content handling

#### 1.2 Content Correction System
**Location**: `openhands-aci/openhands_aci/editor/content_corrector.py`

Implement LLM-assisted content correction similar to Gemini-CLI's `ensureCorrectEdit`:
- Analyze edit context and suggest corrections
- Handle whitespace/indentation issues
- Provide helpful error messages
- Validate edit feasibility

#### 1.3 Enhanced Error Handling
**Location**: `openhands-aci/openhands_aci/editor/gemini_exceptions.py`

Create Gemini-specific error types and handling:
- More descriptive error messages
- Suggestions for fixing common issues
- Context-aware error reporting

### Phase 2: OpenHands Integration

#### 2.1 Create Gemini Tool Definitions
**Location**: `openhands/agenthub/codeact_agent/tools/gemini_tools.py`

Create tool definitions that interface with the openhands-aci implementations:

1. **create_gemini_replace_tool()**
2. **create_gemini_write_file_tool()**
3. **create_gemini_read_file_tool()**

#### 2.2 Model-Specific Tool Selection
**Location**: `openhands/agenthub/codeact_agent/codeact_agent.py`

Modify CodeActAgent to use Gemini tools when Gemini models are detected:
- Check if current LLM is a Gemini model
- Switch to Gemini-optimized tools automatically
- Maintain backward compatibility with existing tools

#### 2.3 Tool Registry Updates
**Location**: `openhands/llm/tool_names.py`

Add new tool names:
- `GEMINI_REPLACE_TOOL_NAME`
- `GEMINI_WRITE_FILE_TOOL_NAME`
- `GEMINI_READ_FILE_TOOL_NAME`

### Phase 3: Advanced Features

#### 3.1 Content Validation
- Implement syntax validation for code files
- Use Gemini for content quality checks
- Provide suggestions for improvements

#### 3.2 Diff Generation and Preview
- Generate unified diffs for changes
- Better visualization of edits
- Integration with IDE preview (future)

#### 3.3 Smart Context Handling
- Automatically include relevant context around edits
- Handle large files intelligently
- Optimize token usage

## Key Design Principles

### 1. Gemini-First Approach
- Leverage Gemini's strengths in understanding context and intent
- Use Gemini for content correction and validation
- Design prompts optimized for Gemini's capabilities

### 2. Graceful Degradation
- Provide helpful error messages and suggestions
- Attempt automatic correction when possible
- Fall back gracefully when corrections aren't possible

### 3. Developer Experience
- Clear, actionable error messages
- Intuitive parameter names and descriptions
- Consistent behavior across tools

### 4. Performance Optimization
- Minimize unnecessary LLM calls
- Cache validation results when appropriate
- Efficient handling of large files

## Implementation Details

### Tool Parameter Design

#### Gemini Replace Tool
```python
{
    "file_path": str,           # Absolute path to file
    "old_string": str,          # Text to replace (more forgiving than current)
    "new_string": str,          # Replacement text
    "expected_replacements": int = 1,  # Number of expected replacements
}
```

#### Gemini Write File Tool
```python
{
    "file_path": str,           # Absolute path to file
    "content": str,             # Complete file content
}
```

#### Gemini Read File Tool
```python
{
    "absolute_path": str,       # Absolute path to file
    "offset": int = None,       # Starting line number
    "limit": int = None,        # Number of lines to read
}
```

### Content Correction Algorithm

1. **Parse Edit Request**: Extract file path, old content, new content
2. **Validate Context**: Check if old_string exists and is unique enough
3. **LLM Correction**: If issues found, use Gemini to suggest corrections
4. **Apply Edit**: Execute the corrected edit
5. **Validate Result**: Ensure edit was successful and makes sense

### Error Recovery Strategies

1. **Fuzzy Matching**: If exact match fails, try fuzzy matching with suggestions
2. **Context Expansion**: Automatically include more context if needed
3. **Alternative Suggestions**: Provide multiple correction options
4. **Rollback Support**: Easy undo functionality

## Testing Strategy

### Unit Tests
- Test each tool individually
- Mock LLM responses for consistent testing
- Cover error cases and edge conditions

### Integration Tests
- Test with real Gemini models
- Verify tool selection logic
- Test backward compatibility

### Performance Tests
- Measure token usage efficiency
- Test with large files
- Benchmark against current tools

## Migration Strategy

### Phase 1: Parallel Implementation
- Implement new tools alongside existing ones
- Use feature flags to control rollout
- Gather feedback from early adopters

### Phase 2: Gradual Rollout
- Enable for specific Gemini models first
- Monitor performance and error rates
- Collect user feedback

### Phase 3: Full Deployment
- Make Gemini tools default for Gemini models
- Maintain existing tools for other models
- Document differences and migration guide

## Success Metrics

1. **Reduced Edit Failures**: Lower rate of failed str_replace operations
2. **Improved User Experience**: Better error messages and suggestions
3. **Higher Success Rate**: More successful file edits on first attempt
4. **Token Efficiency**: Optimal use of Gemini's capabilities

## Future Enhancements

1. **IDE Integration**: Real-time diff previews
2. **Multi-file Operations**: Batch editing across multiple files
3. **Semantic Understanding**: Context-aware editing suggestions
4. **Version Control Integration**: Git-aware editing operations

## Conclusion

This implementation will significantly improve the file editing experience for Gemini users in OpenHands by leveraging Gemini's strengths and following proven patterns from Gemini-CLI. The modular design ensures compatibility while providing superior functionality for Gemini models.

---

## ✅ IMPLEMENTATION COMPLETE

**Status: FULLY IMPLEMENTED AND TESTED** 🎉

The Gemini-optimized tools have been successfully implemented and integrated into OpenHands!

### What was implemented:

1. **Enhanced File Operations** (openhands-aci):
   - `GeminiFileEditor` with intelligent content correction
   - `ContentCorrector` for automatic edit fixing
   - Enhanced error handling with user-friendly messages
   - Content validation and syntax checking

2. **Tool Definitions** (OpenHands):
   - `gemini_read_file` - Enhanced file reading with range support
   - `gemini_write_file` - File writing with validation
   - `gemini_replace` - Intelligent text replacement with correction

3. **Runtime Integration**:
   - Action classes: `GeminiReadFileAction`, `GeminiWriteFileAction`, `GeminiReplaceAction`
   - Function calling integration in `function_calling.py`
   - Runtime execution handlers in `action_execution_server.py`

4. **Automatic Model Detection**:
   - CodeActAgent automatically uses Gemini tools when 'gemini' is detected in model name
   - Seamless fallback to standard tools for other models

### Key Features Implemented:
- ✅ Intelligent content correction (whitespace normalization, context expansion, fuzzy matching)
- ✅ Enhanced error messages with suggestions and similar file detection
- ✅ Content validation for syntax issues
- ✅ Range-based file reading (offset/limit support)
- ✅ Expected replacement count validation
- ✅ Automatic model detection and tool selection
- ✅ Full backward compatibility with existing tools

### Testing Results:
- ✅ All tool definitions working correctly
- ✅ Action creation and dispatch functioning
- ✅ File operations (read/write/replace) working
- ✅ Error handling providing helpful feedback
- ✅ Content correction capabilities verified

### Files Modified/Created:

**openhands-aci:**
- `openhands_aci/editor/content_corrector.py` (NEW)
- `openhands_aci/editor/gemini_exceptions.py` (NEW)
- `openhands_aci/editor/gemini_tools.py` (NEW)

**OpenHands:**
- `openhands/llm/tool_names.py` (MODIFIED - added Gemini tool names)
- `openhands/events/action/files.py` (MODIFIED - added Gemini action classes)
- `openhands/events/action/__init__.py` (MODIFIED - exported new actions)
- `openhands/agenthub/codeact_agent/tools/gemini_tools.py` (NEW)
- `openhands/agenthub/codeact_agent/codeact_agent.py` (MODIFIED - added model detection)
- `openhands/agenthub/codeact_agent/function_calling.py` (MODIFIED - added Gemini tool handling)
- `openhands/runtime/action_execution_server.py` (MODIFIED - added runtime handlers)

The implementation is production-ready and will automatically activate when using Gemini models!
