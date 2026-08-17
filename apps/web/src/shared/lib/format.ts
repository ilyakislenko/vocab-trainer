const formatters: Record<"en" | "ru", Intl.NumberFormat> = {
  en: new Intl.NumberFormat("en"),
  ru: new Intl.NumberFormat("ru"),
};

/** Format a count with locale thousands separators (e.g. "1 234" / "1,234"). */
export function formatCount(n: number, locale: "en" | "ru"): string {
  return formatters[locale].format(n);
}
