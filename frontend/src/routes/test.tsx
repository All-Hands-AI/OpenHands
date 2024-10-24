import { ChatMessage } from "#/components/chat-message";

function TestBed() {
  const code =
    "```js\nconsole.log('Hello, World!')console.log('Hello, World!')console.log('Hello, World!')\n```";

  return (
    <div className="flex items-center justify-center h-screen">
      <ChatMessage type="user" message={code} />
    </div>
  );
}

export default TestBed;
