import type { AgentMessage } from "./types";

export async function streamRunMessages(
  url: string,
  token: string,
  onMessage: (message: AgentMessage) => void,
  onStatus: (status: string) => void,
  signal?: AbortSignal
) {
  const response = await fetch(url, {
    headers: { Authorization: `Bearer ${token}` },
    signal
  });
  if (!response.ok || !response.body) {
    throw new Error(`Unable to stream run: ${response.status}`);
  }
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const events = buffer.split("\n\n");
    buffer = events.pop() || "";
    for (const event of events) {
      const lines = event.split("\n");
      const eventName = lines.find((line) => line.startsWith("event: "))?.slice(7);
      const dataLine = lines.find((line) => line.startsWith("data: "));
      if (!dataLine) continue;
      const data = JSON.parse(dataLine.slice(6));
      if (eventName === "message") {
        onMessage(data as AgentMessage);
      }
      if (eventName === "status") {
        onStatus(data.status as string);
      }
    }
  }
}

