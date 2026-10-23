// Tugmalar (framer-motion’siz – server sahifalarida ham yengil)
import NextLink from "next/link";
import { forwardRef } from "react";

type Variant = "primary" | "secondary" | "ghost" | "dark";
type Size = "md" | "lg" | "sm";

const VARIANTS: Record<Variant, string> = {
  primary:
    "bg-accent-strong text-white shadow-[0_10px_24px_-10px_rgb(var(--accent)/0.7)] hover:bg-accent active:brightness-95",
  secondary: "bg-surface text-ink border border-line hover:border-ink/30 hover:bg-surface-2",
  ghost: "text-ink hover:bg-ink/[0.06]",
  dark: "bg-ink text-page hover:bg-ink/90",
};

const SIZES: Record<Size, string> = {
  sm: "h-9 px-3.5 text-sm gap-1.5",
  md: "h-11 px-5 text-[15px] gap-2",
  lg: "h-14 px-7 text-base gap-2.5",
};

interface ButtonBaseProps {
  variant?: Variant;
  size?: Size;
  className?: string;
  children: React.ReactNode;
}

export function buttonClass(variant: Variant = "primary", size: Size = "md", extra = "") {
  return `focus-ring inline-flex select-none items-center justify-center rounded-btn font-semibold transition-[background,color,border,filter,box-shadow,transform] duration-200 disabled:pointer-events-none disabled:opacity-50 ${VARIANTS[variant]} ${SIZES[size]} ${extra}`;
}

export const Button = forwardRef<
  HTMLButtonElement,
  ButtonBaseProps & React.ButtonHTMLAttributes<HTMLButtonElement>
>(function Button({ variant = "primary", size = "md", className = "", children, ...rest }, ref) {
  return (
    <button ref={ref} className={buttonClass(variant, size, `active:scale-[0.98] ${className}`)} {...rest}>
      {children}
    </button>
  );
});

export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  className = "",
  children,
  ...rest
}: ButtonBaseProps & { href: string } & Omit<React.AnchorHTMLAttributes<HTMLAnchorElement>, "href">) {
  return (
    <NextLink href={href} className={buttonClass(variant, size, `active:scale-[0.98] ${className}`)} {...rest}>
      {children}
    </NextLink>
  );
}

