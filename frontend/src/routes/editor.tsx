import { FileDiffViewer } from "#/components/features/diff-viewer/file-diff-viewer";

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
      <FileDiffViewer
        label="openhands/core/config/llm_config.py"
        original={original}
        modified={modified}
      />
    </main>
  );
}

export default EditorScreen;
