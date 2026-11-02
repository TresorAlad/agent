const BLOCK_PATTERNS = [
  /ignore\s+(all\s+)?(previous|prior)\s+instructions/i,
  /system\s+prompt/i,
  /prix\s+(gratuit|0\s*fcfa)/i,
  /confirme\s+la\s+commande\s+sans/i,
];

export function sanitizeUserInput(text: string): { allowed: boolean; reason?: string } {
  const trimmed = text.trim();
  if (!trimmed) return { allowed: false, reason: "Message vide." };
  for (const pattern of BLOCK_PATTERNS) {
    if (pattern.test(trimmed)) {
      return { allowed: false, reason: "Demande non autorisée." };
    }
  }
  return { allowed: true };
}

export function parseManagerDecision(
  text: string,
  managerPhone: string,
  senderPhone: string,
): { isManager: boolean; approved?: boolean; orderId?: string } {
  const normalizedManager = managerPhone.replace(/\D/g, "");
  const normalizedSender = senderPhone.replace(/\D/g, "");
  if (!normalizedManager || normalizedSender !== normalizedManager) {
    return { isManager: false };
  }
  const upper = text.trim().toUpperCase();
  const match = upper.match(/^(OUI|NON)\s+(CMD-[A-F0-9]+)/);
  if (!match) return { isManager: true };
  return {
    isManager: true,
    approved: match[1] === "OUI",
    orderId: match[2],
  };
}
