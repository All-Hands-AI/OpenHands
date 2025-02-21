import { DiffEditor } from "@monaco-editor/react";

const original = `
import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;
`;

const modified = `
import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";;

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

export default EditorScreen;import { DiffEditor } from "@monaco-editor/react";

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor />
    </main>
  );
}

`;

function EditorScreen() {
  return (
    <main className="h-screen">
      <DiffEditor
        className="w-full h-full"
        language="typescript"
        original={original}
        modified={modified}
        theme="vs-dark"
        options={{
          renderValidationDecorations: "off",
          readOnly: true,
          renderSideBySide: true,
          hideUnchangedRegions: {
            enabled: true,
          },
        }}
      />
    </main>
  );
}

export default EditorScreen;
