// Sertifikatni tekshirish: kodni qo‘lda kiritish
import { Header } from "@/components/Header";
import { VerifyForm } from "@/components/VerifyForm";
import { translate } from "@/i18n/core";
import { serverLang } from "@/lib/serverApi";

export const dynamic = "force-dynamic";

export default async function VerifyIndexPage() {
  const lang = await serverLang();
  const t = (k: string) => translate(lang, k);
  return (
    <>
      <Header />
      <main id="main" className="mx-auto max-w-xl px-4 py-12 sm:px-6 md:py-20">
        <div className="anim-fade-up rounded-panel border border-line bg-surface p-6 shadow-soft sm:p-8">
          <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">{t("verify.enter_title")}</h1>
          <p className="mt-2 text-muted">{t("verify.enter_text")}</p>
          <div className="mt-6">
            <VerifyForm />
          </div>
        </div>
      </main>
    </>
  );
}
