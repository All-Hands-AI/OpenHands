import { render, screen, fireEvent } from "@testing-library/react";
import { ChatInput } from "#/components/chat-input";
import { describe, it, expect, vi } from "vitest";

describe("ChatInput", () => {
  it("should handle text paste correctly", () => {
    const onSubmit = vi.fn();
    const onChange = vi.fn();
    
    render(<ChatInput onSubmit={onSubmit} onChange={onChange} />);
    
    const input = screen.getByTestId("chat-input").querySelector("textarea");
    expect(input).toBeTruthy();
    
    // Fire paste event with text data
    fireEvent.paste(input!, {
      clipboardData: {
        getData: (type: string) => type === 'text/plain' ? 'test paste' : '',
        files: []
      }
    });
  });

  it("should handle image paste correctly", () => {
    const onSubmit = vi.fn();
    const onImagePaste = vi.fn();
    
    render(<ChatInput onSubmit={onSubmit} onImagePaste={onImagePaste} />);
    
    const input = screen.getByTestId("chat-input").querySelector("textarea");
    expect(input).toBeTruthy();
    
    // Create a paste event with an image file
    const file = new File(["dummy content"], "image.png", { type: "image/png" });
    
    // Fire paste event with image data
    fireEvent.paste(input!, {
      clipboardData: {
        getData: () => '',
        files: [file]
      }
    });
    
    // Verify image paste was handled
    expect(onImagePaste).toHaveBeenCalledWith([file]);
  });
});
