import { useState } from "react";
import { streamChat, type AgentMode, type TraceStep } from "./api";
import { ChatPanel } from "./components/ChatPanel";
import { ModeToggle } from "./components/ModeToggle";
import { OrderApproval } from "./components/OrderApproval";
import { TracePanel } from "./components/TracePanel";
import "./App.css";

type ChatMessage = { role: "user" | "assistant"; content: string };

export default function App() {
  const [mode, setMode] = useState<AgentMode>("single");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [trace, setTrace] = useState<TraceStep[]>([]);
  const [elapsedMs, setElapsedMs] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleSend() {
    const text = input.trim();
    if (!text || isLoading) return;

    setError(null);
    setInput("");
    setIsLoading(true);
    setTrace([]);
    setElapsedMs(null);
    const history = messages.map((m) => ({ role: m.role, content: m.content }));
    setMessages((prev) => [...prev, { role: "user", content: text }]);

    let assistantText = "";

    try {
      await streamChat(text, mode, (event) => {
        const type = event.type as string;
        if (type === "delta" && typeof event.content === "string") {
          assistantText += event.content;
        }
        if (type === "trace_step" && event.step) {
          setTrace((prev) => [...prev, event.step as TraceStep]);
        }
        if (type === "trace" && Array.isArray(event.steps)) {
          setTrace(event.steps as TraceStep[]);
        }
        if (type === "agent_complete" && typeof event.elapsed_ms === "number") {
          setElapsedMs(event.elapsed_ms as number);
        }
        if (type === "error") {
          setError(String(event.detail ?? "Erreur agent"));
        }
      }, history);

      if (assistantText.trim()) {
        setMessages((prev) => [...prev, { role: "assistant", content: assistantText.trim() }]);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erreur réseau");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="app-shell">
      <header className="app-header">
        <h1>Boutique intelligente - Dantokpa</h1>
        <p>Agent vendeur WhatsApp (paliers 1-2)</p>
        <ModeToggle mode={mode} onChange={setMode} />
      </header>
      {error && <div className="banner error">{error}</div>}
      <main className="layout">
        <ChatPanel
          messages={messages}
          isLoading={isLoading}
          input={input}
          onInputChange={setInput}
          onSend={handleSend}
        />
        <aside className="side">
          <TracePanel steps={trace} elapsedMs={elapsedMs} />
          <OrderApproval />
        </aside>
      </main>
    </div>
  );
}
