"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { useI18n } from "@/i18n";
import { Button } from "./button";
import { ArrowRight } from "./icons";

// Tekshiruv kodini qo‘lda kiritish
export function VerifyForm({ initial = "" }: { initial?: string }) {
  const { t } = useI18n();
  const router = useRouter();
  const [code, setCode] = useState(initial);

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    const clean = code.toUpperCase().replace(/[^0-9A-Z]/g, "");
    if (clean.length >= 6) router.push(`/verify/${clean}`);
  };

  return (
    <form onSubmit={submit} className="flex flex-col gap-2 sm:flex-row">
      <label htmlFor="verify-code" className="sr-only">
        {t("verify.code")}
      </label>
      <input
        id="verify-code"
        value={code}
        onChange={(e) => setCode(e.target.value.toUpperCase())}
        placeholder={t("verify.placeholder")}
        autoComplete="off"
        autoCapitalize="characters"
        spellCheck={false}
        maxLength={16}
        className="tabular h-12 w-full shrink-0 rounded-btn border sm:flex-1 border-line bg-surface px-4 text-base font-semibold tracking-[0.12em] outline-none transition-[border,box-shadow] placeholder:font-normal placeholder:tracking-normal placeholder:text-muted/70 focus:border-accent focus:ring-4 focus:ring-accent/15"
      />
      <Button type="submit" size="md" className="h-12">
        {t("verify.submit")} <ArrowRight size={17} />
      </Button>
    </form>
  );
}
