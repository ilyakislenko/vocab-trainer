import { useFocusLeeches } from "@/entities/skill-item";
import { useI18n } from "@/shared/lib/i18n";

export function FocusList({ limit = 3 }: { limit?: number }) {
  const { t } = useI18n();
  const focus = useFocusLeeches(limit);

  if (focus.isLoading || !focus.data || focus.data.length === 0) return null;

  return (
    <section className="rounded-3xl border border-destructive/40 bg-destructive/5 p-5">
      <div className="mb-3 flex items-center justify-between gap-3">
        <h2 className="text-lg font-black tracking-tight text-foreground">{t("focus.title")}</h2>
        <span className="rounded-full bg-destructive/10 px-3 py-1 text-sm font-extrabold text-destructive">
          {focus.data.length} {t("focus.leeches")}
        </span>
      </div>
      <ul className="flex flex-wrap gap-2">
        {focus.data.map((item) => (
          <li
            key={item.id}
            className="rounded-full bg-white px-3 py-1 text-sm font-extrabold text-destructive"
          >
            {item.skill}
          </li>
        ))}
      </ul>
    </section>
  );
}
