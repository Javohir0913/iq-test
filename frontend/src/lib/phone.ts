// +998 (XX) XXX-XX-XX niqobi

export function phoneDigits(input: string): string {
  let digits = input.replace(/\D/g, "");
  if (digits.startsWith("998")) digits = digits.slice(3);
  return digits.slice(0, 9);
}

export function formatPhone(input: string): string {
  const d = phoneDigits(input);
  if (!d) return "";
  let out = "+998 (" + d.slice(0, 2);
  if (d.length >= 2) out += ")";
  if (d.length > 2) out += " " + d.slice(2, 5);
  if (d.length > 5) out += "-" + d.slice(5, 7);
  if (d.length > 7) out += "-" + d.slice(7, 9);
  return out;
}

export function normalizePhone(input: string): string {
  const d = phoneDigits(input);
  return d ? `+998${d}` : "";
}

export function isPhoneComplete(input: string): boolean {
  return phoneDigits(input).length === 9;
}
