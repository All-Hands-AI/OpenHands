import React from "react";
import { render, screen } from "@testing-library/react";
import { ChatMessage } from "../../../../src/components/features/chat/chat-message";
import { test, expect, vi, describe } from "vitest";

describe("ChatMessage", () => {
  test("renders a simple message", () => {
    render(<ChatMessage type="user" message="Hello world" />);
    expect(screen.getByText("Hello world")).toBeInTheDocument();
  });

  test("renders a message with newlines", () => {
    const message = "Line 1\nLine 2";
    render(<ChatMessage type="user" message={message} />);
    
    // In markdown, a single newline is preserved in the paragraph
    const element = screen.getByText((content, element) => {
      return element.tagName.toLowerCase() === 'p' && 
             element.textContent.includes('Line 1') && 
             element.textContent.includes('Line 2');
    });
    expect(element).toBeInTheDocument();
    expect(element.tagName).toBe("P");
  });

  test("renders a message with double newlines as separate paragraphs", () => {
    const message = "Paragraph 1\n\nParagraph 2";
    render(<ChatMessage type="user" message={message} />);
    
    // In markdown, double newlines create separate paragraphs
    const paragraph1 = screen.getByText("Paragraph 1");
    const paragraph2 = screen.getByText("Paragraph 2");
    
    expect(paragraph1).toBeInTheDocument();
    expect(paragraph2).toBeInTheDocument();
    
    // They should be in separate paragraph elements
    expect(paragraph1.tagName).toBe("P");
    expect(paragraph2.tagName).toBe("P");
  });

  test("renders a message with markdown formatting", () => {
    const message = "**Bold text** and *italic text*";
    render(<ChatMessage type="user" message={message} />);
    
    const boldElement = screen.getByText("Bold text");
    const italicElement = screen.getByText("italic text");
    
    expect(boldElement).toBeInTheDocument();
    expect(italicElement).toBeInTheDocument();
    
    expect(boldElement.tagName).toBe("STRONG");
    expect(italicElement.tagName).toBe("EM");
  });
});