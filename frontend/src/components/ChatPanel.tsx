type Message = {
  role: "user" | "assistant";
  content: string;
};

type Props = {
  messages: Message[];
  isLoading: boolean;
  input: string;
  onInputChange: (value: string) => void;
  onSend: () => void;
};

export function ChatPanel({ messages, isLoading, input, onInputChange, onSend }: Props) {
  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || isLoading) return;
    onSend();
  }

  return (
    <section className="chat-panel">
      <div className="chat-header">
        <div className="avatar">TD</div>
        <div>
          <strong>Tissus Dantokpa</strong>
          <p className="subtitle">Vendeur WhatsApp (simulation)</p>
        </div>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <p className="hint">
            Exemple : « Je veux 2 pagnes wax bleu livrés à Akpakpa, prix en euros »
          </p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`bubble ${msg.role}`}>
            {msg.content}
          </div>
        ))}
        {isLoading && <div className="bubble assistant typing">Le vendeur réfléchit...</div>}
      </div>
      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          value={input}
          onChange={(e) => onInputChange(e.target.value)}
          placeholder="Votre message..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          Envoyer
        </button>
      </form>
    </section>
  );
}
