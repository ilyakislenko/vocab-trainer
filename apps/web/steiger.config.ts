import fsd from "@feature-sliced/steiger-plugin";
import { defineConfig } from "steiger";

export default defineConfig([
  ...fsd.configs.recommended,
  {
    // These three rules are stylistic/advisory, not boundary enforcement —
    // the rules that actually protect the architecture (forbidden-imports,
    // public-api, no-public-api-sidestep, no-layer-public-api, ...) stay on
    // via the recommended config above.
    //
    // - inconsistent-naming flags `entities/stats` as "plural" next to the
    //   singular `entities/card` and `entities/deck`; "stats" (like
    //   "settings"/"analytics") is a mass noun in this domain, not a plural
    //   of "stat".
    // - insignificant-slice suggests merging every entity/feature into the
    //   widget that is its only current consumer; that per-concern slicing
    //   (entities/card, features/rate-card, widgets/review-session, etc.)
    //   is the deliberate layering from the approved design, not accidental
    //   fragmentation.
    // - segments-by-purpose objects to the unsliced `app/providers.tsx`
    //   file name; it is the app-layer composition root's provider wiring,
    //   already named for its one purpose.
    rules: {
      "fsd/inconsistent-naming": "off",
      "fsd/insignificant-slice": "off",
      "fsd/segments-by-purpose": "off",
    },
  },
]);
