"""Enhanced editor key bindings for OpenHands CLI.

This module provides comprehensive vi and emacs style editing capabilities
for the CLI interface, including common shortcuts and editing commands.
"""

from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.key_binding.key_processor import KeyPressEvent
from prompt_toolkit.keys import Keys


def create_emacs_key_bindings() -> KeyBindings:
    """Create enhanced emacs-style key bindings for CLI input.
    
    Provides common emacs shortcuts:
    - Ctrl+A: Beginning of line
    - Ctrl+E: End of line
    - Ctrl+K: Kill (delete) from cursor to end of line
    - Ctrl+U: Kill from beginning of line to cursor
    - Ctrl+W: Kill word backwards
    - Alt+D: Kill word forwards
    - Ctrl+Y: Yank (paste) killed text
    - Ctrl+T: Transpose characters
    - Alt+T: Transpose words
    - Ctrl+F: Forward character
    - Ctrl+B: Backward character
    - Alt+F: Forward word
    - Alt+B: Backward word
    - Ctrl+D: Delete character forward
    - Ctrl+H: Delete character backward
    - Ctrl+L: Clear screen
    """
    kb = KeyBindings()
    
    # Movement commands
    @kb.add('c-a')
    def _(event: KeyPressEvent) -> None:
        """Move to beginning of line."""
        event.current_buffer.cursor_position = 0
    
    @kb.add('c-e')
    def _(event: KeyPressEvent) -> None:
        """Move to end of line."""
        event.current_buffer.cursor_position = len(event.current_buffer.text)
    
    @kb.add('c-f')
    def _(event: KeyPressEvent) -> None:
        """Move forward one character."""
        event.current_buffer.cursor_right()
    
    @kb.add('c-b')
    def _(event: KeyPressEvent) -> None:
        """Move backward one character."""
        event.current_buffer.cursor_left()
    
    @kb.add('escape', 'f')
    def _(event: KeyPressEvent) -> None:
        """Move forward one word."""
        event.current_buffer.cursor_right(count=event.current_buffer.document.find_next_word_ending())
    
    @kb.add('escape', 'b')
    def _(event: KeyPressEvent) -> None:
        """Move backward one word."""
        event.current_buffer.cursor_left(count=event.current_buffer.document.find_previous_word_beginning())
    
    # Deletion commands
    @kb.add('c-k')
    def _(event: KeyPressEvent) -> None:
        """Kill from cursor to end of line."""
        buffer = event.current_buffer
        deleted = buffer.delete(count=len(buffer.text) - buffer.cursor_position)
        buffer.clipboard.set_text(deleted)
    
    @kb.add('c-u')
    def _(event: KeyPressEvent) -> None:
        """Kill from beginning of line to cursor."""
        buffer = event.current_buffer
        deleted = buffer.delete(count=-buffer.cursor_position)
        buffer.clipboard.set_text(deleted)
    
    @kb.add('c-w')
    def _(event: KeyPressEvent) -> None:
        """Kill word backwards."""
        buffer = event.current_buffer
        pos = buffer.document.find_previous_word_beginning()
        if pos:
            deleted = buffer.delete(count=pos)
            buffer.clipboard.set_text(deleted)
    
    @kb.add('escape', 'd')
    def _(event: KeyPressEvent) -> None:
        """Kill word forwards."""
        buffer = event.current_buffer
        pos = buffer.document.find_next_word_ending()
        if pos:
            deleted = buffer.delete(count=pos)
            buffer.clipboard.set_text(deleted)
    
    @kb.add('c-d')
    def _(event: KeyPressEvent) -> None:
        """Delete character forward."""
        event.current_buffer.delete()
    
    @kb.add('c-h')
    def _(event: KeyPressEvent) -> None:
        """Delete character backward."""
        event.current_buffer.delete_before_cursor()
    
    # Yank (paste) command
    @kb.add('c-y')
    def _(event: KeyPressEvent) -> None:
        """Yank (paste) killed text."""
        event.current_buffer.paste_clipboard_data(event.current_buffer.clipboard.get_data())
    
    # Transpose commands
    @kb.add('c-t')
    def _(event: KeyPressEvent) -> None:
        """Transpose characters."""
        buffer = event.current_buffer
        if buffer.cursor_position > 0 and len(buffer.text) > 1:
            pos = buffer.cursor_position
            if pos == len(buffer.text):
                pos -= 1
            if pos > 0:
                char1 = buffer.text[pos - 1]
                char2 = buffer.text[pos]
                new_text = (
                    buffer.text[:pos - 1] + 
                    char2 + char1 + 
                    buffer.text[pos + 1:]
                )
                buffer.text = new_text
                buffer.cursor_position = pos + 1
    
    @kb.add('escape', 't')
    def _(event: KeyPressEvent) -> None:
        """Transpose words."""
        buffer = event.current_buffer
        doc = buffer.document
        
        # Find current word boundaries
        word_start = doc.find_previous_word_beginning()
        word_end = doc.find_next_word_ending()
        
        if word_start and word_end:
            current_word = buffer.text[doc.cursor_position + word_start:doc.cursor_position + word_end]
            
            # Find previous word
            prev_word_start = doc.find_previous_word_beginning(count=2)
            prev_word_end = doc.find_previous_word_beginning()
            
            if prev_word_start and prev_word_end:
                prev_word = buffer.text[doc.cursor_position + prev_word_start:doc.cursor_position + prev_word_end]
                
                # Swap the words
                new_text = (
                    buffer.text[:doc.cursor_position + prev_word_start] +
                    current_word +
                    buffer.text[doc.cursor_position + prev_word_end:doc.cursor_position + word_start] +
                    prev_word +
                    buffer.text[doc.cursor_position + word_end:]
                )
                buffer.text = new_text
                buffer.cursor_position = doc.cursor_position + word_end
    
    # Clear screen
    @kb.add('c-l')
    def _(event: KeyPressEvent) -> None:
        """Clear screen."""
        event.app.renderer.clear()
    
    return kb


def create_vi_key_bindings() -> KeyBindings:
    """Create enhanced vi-style key bindings for CLI input.
    
    Note: prompt_toolkit already provides comprehensive vi mode support.
    This function adds any additional custom vi bindings if needed.
    """
    kb = KeyBindings()
    
    # Vi mode is primarily handled by prompt_toolkit's built-in vi_mode=True
    # We can add custom bindings here if needed for specific OpenHands functionality
    
    return kb


def create_enhanced_key_bindings(editor_mode: str) -> KeyBindings:
    """Create enhanced key bindings based on the specified editor mode.
    
    Args:
        editor_mode: Either 'emacs' or 'vi'
        
    Returns:
        KeyBindings object with appropriate bindings
    """
    if editor_mode == 'vi':
        return create_vi_key_bindings()
    else:  # emacs mode (default)
        return create_emacs_key_bindings()