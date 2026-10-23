"use client";

import { Header } from "@/components/Header";
import { Grid3 } from "@/components/shapes";
import { ButtonLink } from "@/components/button";
import { StateView } from "@/components/state-view";
import { useI18n } from "@/i18n";

export default function NotFound() {
  const { t } = useI18n();
  return (
    <>
      <Header />
      <main id="main">
        <StateView icon={<Grid3 size={48} filled={[0, 4]} accent={8} />} title={t("errors.not_found_title")} text={t("errors.not_found_text")}>
          <ButtonLink href="/">{t("common.home")}</ButtonLink>
        </StateView>
      </main>
    </>
  );
}
