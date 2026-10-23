// Urinish tokenlari va oflayn navbat brauzer xotirasida saqlanadi.
// Xotira mavjud bo‘lmasa (maxfiy rejim va h.k.) jimgina ishlamay qoladi.

const ATTEMPTS_KEY = "iq.attempts";
const CURRENT_KEY = "iq.current";

export interface StoredAttempt {
  id: string;
  token: string;
  createdAt: number;
}

function read<T>(key: string, fallback: T): T {
  try {
    const raw = localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : fallback;
  } catch {
    return fallback;
  }
}

function write(key: string, value: unknown) {
  try {
    if (value === undefined) localStorage.removeItem(key);
    else localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* e’tiborsiz */
  }
}

export const storage = {
  /** Bot havolasidagi `?t=token` ni saqlab, manzildan olib tashlaydi (token tarixda qolmasin). */
  adoptUrlToken(id: string, makeCurrent = false) {
    try {
      const url = new URL(window.location.href);
      const token = url.searchParams.get("t");
      if (!token) return;
      const all = read<Record<string, StoredAttempt>>(ATTEMPTS_KEY, {});
      all[id] = { id, token, createdAt: all[id]?.createdAt ?? Date.now() };
      write(ATTEMPTS_KEY, all);
      if (makeCurrent) write(CURRENT_KEY, id);
      url.searchParams.delete("t");
      window.history.replaceState(window.history.state, "", url.pathname + url.search + url.hash);
    } catch {
      /* e’tiborsiz */
    }
  },
  /** Tokenni saqlaydi, joriy urinishni o‘zgartirmaydi */
  remember(id: string, token: string) {
    const all = read<Record<string, StoredAttempt>>(ATTEMPTS_KEY, {});
    if (all[id]?.token === token) return;
    all[id] = { id, token, createdAt: all[id]?.createdAt ?? Date.now() };
    write(ATTEMPTS_KEY, all);
  },
  saveAttempt(id: string, token: string) {
    const all = read<Record<string, StoredAttempt>>(ATTEMPTS_KEY, {});
    all[id] = { id, token, createdAt: Date.now() };
    write(ATTEMPTS_KEY, all);
    write(CURRENT_KEY, id);
  },
  token(id: string): string | null {
    return read<Record<string, StoredAttempt>>(ATTEMPTS_KEY, {})[id]?.token ?? null;
  },
  current(): StoredAttempt | null {
    const id = read<string | null>(CURRENT_KEY, null);
    if (!id) return null;
    return read<Record<string, StoredAttempt>>(ATTEMPTS_KEY, {})[id] ?? null;
  },
  clearCurrent(id?: string) {
    const cur = read<string | null>(CURRENT_KEY, null);
    if (!id || cur === id) write(CURRENT_KEY, undefined);
  },
  position(id: string): number {
    return read<number>(`iq.pos.${id}`, 0);
  },
  setPosition(id: string, index: number) {
    write(`iq.pos.${id}`, index);
  },
  pending(id: string): Record<string, string | null> {
    return read<Record<string, string | null>>(`iq.pending.${id}`, {});
  },
  setPending(id: string, pending: Record<string, string | null>) {
    write(`iq.pending.${id}`, Object.keys(pending).length ? pending : undefined);
  },
};
