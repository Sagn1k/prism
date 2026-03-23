import { useEffect, useState } from "react";
import { spectrumApi, type SpectrumData } from "@/lib/api";

export function useSpectrum() {
  const [spectrum, setSpectrum] = useState<SpectrumData | null>(null);
  const [loading, setLoading] = useState(true);

  const fetch = async () => {
    try {
      const res = await spectrumApi.get();
      setSpectrum(res.data);
    } catch {
      /* not logged in or no data yet */
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetch();
  }, []);

  return { spectrum, loading, refetch: fetch };
}
