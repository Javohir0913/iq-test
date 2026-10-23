// Bo‘sh / xato / topilmadi holatlari uchun umumiy ko‘rinish (CSS animatsiya)

// --- StateView: bo‘sh / xato / topilmadi holatlari --------------------------------

export function StateView({
  icon,
  title,
  text,
  children,
}: {
  icon?: React.ReactNode;
  title: string;
  text?: string;
  children?: React.ReactNode;
}) {
  return (
    <div className="anim-fade-up mx-auto flex max-w-md flex-col items-center px-4 py-16 text-center">
      {icon && (
        <div className="mb-6 grid h-24 w-24 place-items-center rounded-panel border border-line bg-panel text-ink">
          {icon}
        </div>
      )}
      <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
      {text && <p className="mt-2 text-muted">{text}</p>}
      {children && <div className="mt-7 flex flex-wrap justify-center gap-3">{children}</div>}
    </div>
  );
}
