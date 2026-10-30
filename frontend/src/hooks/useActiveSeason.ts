import { useEffect, useState } from "react";
import { getSeasons } from "../services/api";

/**
 * A shared season selection broadcast through the f1-season-change event.
 * Keeps pages in sync with the season selector in the sidebar without adding
 * a global state dependency.
 */
export function useActiveSeason(): number {
  const [season, setSeason] = useState(2023);

  useEffect(() => {
    let mounted = true;
    getSeasons()
      .then((years) => {
        if (!mounted || !years.length) return;
        setSeason((current) => years.includes(current) ? current : years[0]);
      })
      .catch(() => {
        // Keep the useful 2023 fallback if the seasons endpoint is unavailable.
      });

    const onSeasonChange = (event: Event) => {
      const value = (event as CustomEvent<number>).detail;
      if (Number.isInteger(value) && value >= 1950) setSeason(value);
    };
    window.addEventListener("f1-season-change", onSeasonChange);
    return () => {
      mounted = false;
      window.removeEventListener("f1-season-change", onSeasonChange);
    };
  }, []);

  return season;
}
