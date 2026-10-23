import type { Metadata, Viewport } from "next";
import { cookies } from "next/headers";
import "./globals.css";
import { I18nProvider } from "@/i18n";
import { LANG_COOKIE, translate, type Lang } from "@/i18n/core";
import { ThemeProvider } from "@/lib/theme";
import { themeInitScript } from "@/lib/themeScript";
import { AuthProvider } from "@/lib/auth";
import { TelegramProvider } from "@/lib/telegram";

async function getLang(): Promise<Lang> {
  const value = (await cookies()).get(LANG_COOKIE)?.value;
  return value === "ru" ? "ru" : "uz";
}

export async function generateMetadata(): Promise<Metadata> {
  const lang = await getLang();
  return {
    title: translate(lang, "meta.title"),
    description: translate(lang, "meta.description"),
    applicationName: translate(lang, "common.brand"),
    icons: { icon: "/icon.svg" },
  };
}

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
  viewportFit: "cover",
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#FBFAF7" },
    { media: "(prefers-color-scheme: dark)", color: "#0C121D" },
  ],
};

export default async function RootLayout({ children }: { children: React.ReactNode }) {
  const lang = await getLang();
  return (
    <html lang={lang} suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        <link rel="preload" href="/fonts/inter-latin.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        {lang === "ru" && (
          <link rel="preload" href="/fonts/inter-cyrillic.woff2" as="font" type="font/woff2" crossOrigin="anonymous" />
        )}
      </head>
      <body className="min-h-dvh font-sans antialiased">
        <I18nProvider initialLang={lang}>
          <ThemeProvider>
            <TelegramProvider>
              <AuthProvider>{children}</AuthProvider>
            </TelegramProvider>
          </ThemeProvider>
        </I18nProvider>
      </body>
    </html>
  );
}
