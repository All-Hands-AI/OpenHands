export async function streamChat(messages: { role: string; content: string }[], model?: string, onToken?: (t: string) => void): Promise<void> {
  const res = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ messages, model, stream: true }),
  });
  if (!res.body) return;
  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    let idx;
    while ((idx = buffer.indexOf("\n\n")) !== -1) {
      const eventChunk = buffer.slice(0, idx);
      buffer = buffer.slice(idx + 2);
      const lines = eventChunk.split("\n");
      let data = "";
      for (const line of lines) {
        if (line.startsWith("data:")) {
          data += line.slice(5).trimStart();
        }
      }
      if (data && onToken) onToken(data);
    }
  }
}

export async function startImageJob(prompt: string): Promise<string> {
  const res = await fetch("/api/generate-image", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const j = await res.json();
  return j.job_id as string;
}

export async function startVideoJob(prompt: string): Promise<string> {
  const res = await fetch("/api/generate-video", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ prompt }),
  });
  const j = await res.json();
  return j.job_id as string;
}

export async function getJob(jobId: string): Promise<any> {
  const res = await fetch(`/api/jobs/${jobId}`);
  return await res.json();
}