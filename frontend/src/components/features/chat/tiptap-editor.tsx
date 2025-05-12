import React, { useEffect, useCallback, useState } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Mention } from "@tiptap/extension-mention";
import Placeholder from "@tiptap/extension-placeholder";
import tippy from "tippy.js";
import "tippy.js/dist/tippy.css";
import { cn } from "#/utils/utils";
import "./tiptap-editor.css";

export interface MicroagentInfo {
  name: string;
  trigger: string;
  description: string;
}

interface TipTapEditorProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: (value: string) => void;
  onFocus?: () => void;
  onBlur?: () => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
}

export function TipTapEditor({
  value,
  onChange,
  onSubmit,
  onFocus,
  onBlur,
  placeholder = "What would you like to build?",
  disabled = false,
  className,
}: TipTapEditorProps) {
  const [microagents, setMicroagents] = useState<MicroagentInfo[]>([]);
  const [loading, setLoading] = useState(false);

  // Fetch microagents when the component mounts
  useEffect(() => {
    const fetchMicroagents = async () => {
      try {
        setLoading(true);
        const response = await fetch("/api/options/microagents");
        if (response.ok) {
          const data = await response.json();
          setMicroagents(data);
        }
      } catch (error) {
        console.error("Error fetching microagents:", error);
      } finally {
        setLoading(false);
      }
    };

    fetchMicroagents();
  }, []);

  // Custom suggestion handler for microagents using tippy.js
  const suggestionHandler = useCallback(() => {
    return {
      char: "/",
      items: ({ query }: { query: string }) => {
        if (!query) return microagents;

        return microagents.filter(
          (item) =>
            item.trigger.toLowerCase().includes(query.toLowerCase()) ||
            item.name.toLowerCase().includes(query.toLowerCase())
        );
      },
      render: () => {
        let popup: any = null;

        return {
          onStart: (props: any) => {
            popup = tippy("body", {
              getReferenceClientRect: props.clientRect,
              appendTo: () => document.body,
              content: renderItems(props),
              showOnCreate: true,
              interactive: true,
              trigger: "manual",
              placement: "bottom-start",
              theme: "microagent",
              arrow: false,
              zIndex: 9999,
            });
          },
          onUpdate: (props: any) => {
            popup[0].setProps({
              getReferenceClientRect: props.clientRect,
              content: renderItems(props),
            });
          },
          onKeyDown: (props: any) => {
            if (props.event.key === "Escape") {
              popup[0].hide();
              return true;
            }
            
            // Handle arrow keys and Enter for selection
            if (["ArrowUp", "ArrowDown", "Enter"].includes(props.event.key)) {
              return true;
            }
            
            return false;
          },
          onExit: () => {
            popup && popup[0].destroy();
            popup = null;
          },
        };
      },
      command: ({ editor, range, props }: any) => {
        // Insert the selected microagent trigger
        editor
          .chain()
          .focus()
          .deleteRange(range)
          .insertContent(`${props.trigger.replace("/", "")} `)
          .run();
      },
    };
  }, [microagents, loading]);

  // Render the suggestion items
  const renderItems = useCallback((props: any) => {
    const container = document.createElement("div");
    container.classList.add("microagent-suggestions-container");

    if (loading) {
      container.innerHTML = '<div class="p-2 text-neutral-400">Loading microagents...</div>';
      return container;
    }

    if (props.items.length === 0) {
      container.innerHTML = '<div class="p-2 text-neutral-400">No microagents found</div>';
      return container;
    }

    container.innerHTML = `
      <div class="microagent-list">
        ${props.items
          .map(
            (item: MicroagentInfo, index: number) => `
            <div 
              class="microagent-item ${index === props.selectedIndex ? "is-selected" : ""}"
              data-index="${index}"
            >
              <span class="microagent-trigger">${item.trigger}</span>
              <span class="microagent-description">${item.description}</span>
            </div>
          `
          )
          .join("")}
      </div>
    `;

    // Add click event listeners
    const items = container.querySelectorAll(".microagent-item");
    items.forEach((item: Element, index: number) => {
      item.addEventListener("click", () => {
        props.command(props.items[index]);
      });
    });

    return container;
  }, [loading]);

  const tipTapEditor = useEditor({
    extensions: [
      StarterKit,
      Placeholder.configure({
        placeholder,
        emptyEditorClass: "is-editor-empty",
      }),
      Mention.configure({
        HTMLAttributes: {
          class: "microagent-mention",
        },
        suggestion: suggestionHandler(),
        renderLabel: ({ node }) => node.attrs.label,
      }),
    ],
    content: value,
    onUpdate: ({ editor: editorInstance }) => {
      onChange(editorInstance.getText());
    },
    editorProps: {
      attributes: {
        class: cn(
          "prose prose-sm focus:outline-none w-full max-w-full",
          "text-white placeholder:text-neutral-400",
          className,
        ),
      },
      // eslint-disable-next-line consistent-return
      handleKeyDown: (view, event) => {
        // Handle Enter key for submission
        if (event.key === "Enter" && !event.shiftKey && !disabled) {
          event.preventDefault();
          const text = view.state.doc.textContent;
          if (text.trim()) {
            onSubmit(text);
            // Clear the editor
            view.dispatch(view.state.tr.delete(0, view.state.doc.content.size));
          }
          return true;
        }
        // Must return false for other keys
        return false;
      },
    },
  });

  // Update editor content when value prop changes
  useEffect(() => {
    if (tipTapEditor && tipTapEditor.getText() !== value) {
      tipTapEditor.commands.setContent(value);
    }
  }, [value, tipTapEditor]);

  // Handle focus and blur events
  useEffect(() => {
    if (!tipTapEditor) return;

    const handleFocus = () => {
      if (onFocus) onFocus();
    };

    const handleBlur = () => {
      if (onBlur) onBlur();
    };

    tipTapEditor.on("focus", handleFocus);
    tipTapEditor.on("blur", handleBlur);

    // eslint-disable-next-line consistent-return
    return () => {
      tipTapEditor.off("focus", handleFocus);
      tipTapEditor.off("blur", handleBlur);
    };
  }, [tipTapEditor, onFocus, onBlur]);

  return (
    <EditorContent
      editor={tipTapEditor}
      className={cn(
        "grow text-sm self-center resize-none outline-none ring-0",
        "transition-all duration-200 ease-in-out",
        "bg-transparent",
        className,
      )}
    />
  );
}
