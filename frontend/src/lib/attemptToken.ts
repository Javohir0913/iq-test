// Urinish tokenini topish: brauzer xotirasi → bot havolasi (?t=) → Telegram akkaunti (boshqa qurilma)
import { authApi } from "./api";
import { storage } from "./storage";

export async function resolveAttemptToken(id: string, authed: boolean, makeCurrent = false): Promise<string | null> {
  storage.adoptUrlToken(id, makeCurrent);
  const local = storage.token(id);
  if (local || !authed) return local;
  try {
    const { attempts } = await authApi.myAttempts();
    for (const a of attempts) storage.remember(a.attempt_id, a.token);
    return storage.token(id);
  } catch {
    return null;
  }
}
