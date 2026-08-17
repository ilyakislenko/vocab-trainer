import { readdirSync, readFileSync, statSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";

// Guards dark-mode contrast (Spec E): a literal `bg-white` surface stays white
// when the `dark` class flips the theme, so paired with a light token
// (`text-foreground` etc.) it renders invisible text. The translucent
// variants `bg-white/90`/`bg-white/15` are deliberately excluded — they sit on
// explicitly-colored backdrops (`text-black`, a permanent dark video overlay).
const SRC = join(import.meta.dirname, "..", "..", "src");

function sourceFiles(dir: string): string[] {
  const files: string[] = [];
  for (const entry of readdirSync(dir)) {
    const full = join(dir, entry);
    if (statSync(full).isDirectory()) {
      files.push(...sourceFiles(full));
    } else if (/\.tsx?$/.test(entry) && !/\.test\.tsx?$/.test(entry)) {
      files.push(full);
    }
  }
  return files;
}

describe("theme surfaces", () => {
  it("uses theme tokens instead of literal white surfaces", () => {
    const offenders: string[] = [];
    for (const file of sourceFiles(SRC)) {
      const content = readFileSync(file, "utf8");
      if (/(^|[^-])bg-white(?![-\w/])/.test(content)) {
        offenders.push(file);
      }
    }
    expect(offenders).toEqual([]);
  });
});
