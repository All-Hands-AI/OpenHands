import React, { useEffect, useCallback, useState } from "react";
import { useEditor, EditorContent } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";
import { Mention } from "@tiptap/extension-mention";
import Placeholder from "@tiptap/extension-placeholder";
import { createRoot } from "react-dom/client";
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
        // Error fetching microagents
      } finally {
        setLoading(false);
      }
    };

    fetchMicroagents();
  }, []);

  // Custom suggestion handler for microagents
  const suggestionHandler = useCallback(
    () => ({
      char: "/",
      items: ({ query }: { query: string }) => {
        if (!query) return microagents;

        return microagents.filter(
          (item) =>
            item.trigger.toLowerCase().includes(query.toLowerCase()) ||
            item.name.toLowerCase().includes(query.toLowerCase()),
        );
      },
      render: () => {
        let popup: HTMLElement | null = null;
        let component: React.ReactNode | null = null;

        return {
          onStart: (props: {
            items: MicroagentInfo[];
            selectedIndex: number;
            command: (item: MicroagentInfo) => void;
          }) => {
            popup = document.createElement("div");
            popup.classList.add("microagent-suggestions-popup");
            document.body.appendChild(popup);

            component = (
              <div className="absolute z-50 bg-neutral-800 rounded-md shadow-lg border border-neutral-600 w-64 max-h-60 overflow-y-auto">
                {loading && (
                  <div className="p-2 text-neutral-400">
                    Loading microagents...
                  </div>
                )}
                {!loading && props.items.length === 0 && (
                  <div className="p-2 text-neutral-400">
                    No microagents found
                  </div>
                )}
                {!loading && props.items.length > 0 && (
                  <ul className="py-1">
                    {props.items.map((item: MicroagentInfo, index: number) => (
                      <div
                        key={item.trigger}
                        className={cn(
                          "px-3 py-2 hover:bg-neutral-700 cursor-pointer flex flex-col",
                          index === props.selectedIndex ? "bg-neutral-700" : "",
                        )}
                        onClick={() => props.command(item)}
                      >
                        <span className="font-medium text-white">
                          {item.trigger}
                        </span>
                        <span className="text-xs text-neutral-400 truncate">
                          {item.description}
                        </span>
                      </div>
                    ))}
                  </ul>
                )}
              </div>
            );

            if (popup) {
              const { clientRect } = props;
              const { top, left } = clientRect();

              // Position the popup
              popup.style.position = "absolute";
              popup.style.top = `${top}px`;
              popup.style.left = `${left}px`;

              // Render the component into the popup
              const root = createRoot(popup);
              root.render(component);
            }
          },
          onUpdate: (props: {
            items: MicroagentInfo[];
            selectedIndex: number;
            clientRect: () => { top: number; left: number };
          }) => {
            if (popup) {
              const { clientRect } = props;
              const { top, left } = clientRect();

              // Update position
              popup.style.top = `${top}px`;
              popup.style.left = `${left}px`;

              // Re-render with updated props
              const root = createRoot(popup);
              root.render(component);
            }
          },
          onKeyDown: (props: { event: KeyboardEvent }) => {
            if (props.event.key === "Escape") {
              props.event.preventDefault();
              return true;
            }

            return false;
          },
          onExit: () => {
            if (popup) {
              document.body.removeChild(popup);
              popup = null;
              component = null;
            }
          },
        };
      },
      command: ({
        editor,
        range,
        props,
      }: {
        editor: {
          chain: () => {
            focus: () => {
              deleteRange: (range: { from: number; to: number }) => {
                insertContent: (content: string) => { run: () => void };
              };
            };
          };
        };
        range: { from: number; to: number };
        props: MicroagentInfo;
      }) => {
        // Insert the selected microagent trigger
        editor
          .chain()
          .focus()
          .deleteRange(range)
          .insertContent(`${props.trigger.replace("/", "")} `)
          .run();
      },
    }),
    [microagents, loading],
  );

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
