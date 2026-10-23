"use client";

import { Header } from "@/components/Header";
import { Refresh } from "@/components/icons";
import { Triangle } from "@/components/shapes";
import { Button } from "@/components/button";
import { StateView } from "@/components/state-view";
import { useI18n } from "@/i18n";

export default function ErrorPage({ reset }: { error: Error; reset: () => void }) {
  const { t } = useI18n();
  return (
    <>
      <Header />
      <main id="main">
        <StateView icon={<Triangle size={44} className="text-accent" />} title={t("errors.generic_title")} text={t("errors.generic_text")}>
          <Button onClick={reset}>
            <Refresh size={16} /> {t("common.retry")}
          </Button>
        </StateView>
      </main>
    </>
  );
}
