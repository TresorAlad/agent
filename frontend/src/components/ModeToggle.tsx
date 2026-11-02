import type { AgentMode } from "../api";

type Props = {
  mode: AgentMode;
  onChange: (mode: AgentMode) => void;
};

export function ModeToggle({ mode, onChange }: Props) {
  return (
    <div className="mode-toggle">
      <span className="mode-label">Mode agent</span>
      <button
        type="button"
        className={mode === "single" ? "active" : ""}
        onClick={() => onChange("single")}
      >
        Vendeur seul
      </button>
      <button
        type="button"
        className={mode === "team" ? "active" : ""}
        onClick={() => onChange("team")}
      >
        Équipe (Gérant)
      </button>
    </div>
  );
}
