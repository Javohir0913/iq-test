// Server va klient uchun umumiy (React'siz) tarjima funksiyalari
import uz from "./uz.json";
import ru from "./ru.json";

export type Lang = "uz" | "ru";
export const LANGS: Lang[] = ["uz", "ru"];
export const LANG_COOKIE = "lang";

const DICTS: Record<Lang, unknown> = { uz, ru };

export type Vars = Record<string, string | number>;

function lookup(dict: unknown, key: string): unknown {
  return key.split(".").reduce<unknown>((node, part) => {
    if (node && typeof node === "object") return (node as Record<string, unknown>)[part];
    return undefined;
  }, dict);
}

function interpolate(text: string, vars?: Vars) {
  if (!vars) return text;
  return text.replace(/\{(\w+)\}/g, (_, name) => (name in vars ? String(vars[name]) : `{${name}}`));
}

export function translate(lang: Lang, key: string, vars?: Vars): string {
  let value = lookup(DICTS[lang], key);
  if (value === undefined) value = lookup(DICTS.uz, key);
  if (value && typeof value === "object" && !Array.isArray(value)) {
    // Ko‘plik shakllari: { one, few, many, other }
    const n = Number(vars?.n ?? vars?.count ?? 0);
    const rule = new Intl.PluralRules(lang).select(n);
    const forms = value as Record<string, string>;
    value = forms[rule] ?? forms.other;
  }
  if (typeof value !== "string") return key;
  return interpolate(value, vars);
}

export function translateList<T = string>(lang: Lang, key: string): T[] {
  const value = lookup(DICTS[lang], key) ?? lookup(DICTS.uz, key);
  return Array.isArray(value) ? (value as T[]) : [];
}

