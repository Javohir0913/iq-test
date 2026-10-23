"use client";

import { useEffect } from "react";

// `.reveal` elementlari ko‘rinish maydoniga kirganda `.is-in` klassini oladi
export function RevealScope() {
  useEffect(() => {
    const els = Array.from(document.querySelectorAll<HTMLElement>(".reveal:not(.is-in)"));
    if (!("IntersectionObserver" in window)) {
      els.forEach((el) => el.classList.add("is-in"));
      return;
    }
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            e.target.classList.add("is-in");
            io.unobserve(e.target);
          }
        });
      },
      { rootMargin: "0px 0px -60px 0px" },
    );
    els.forEach((el) => io.observe(el));
    return () => io.disconnect();
  }, []);
  return (
    <noscript>
      <style>{`.reveal{opacity:1!important;transform:none!important}`}</style>
    </noscript>
  );
}
