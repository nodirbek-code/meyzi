"use client";

import { useCallback, useEffect, useState } from "react";

import { api, ClientApiError } from "@/lib/client";

/** Kabinet ro'yxatlari uchun: yuklash + qayta yuklash + xato. */
export function useData<T>(path: string | null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const reload = useCallback(async () => {
    if (!path) return;
    setLoading(true);
    try {
      setData(await api.get<T>(path));
      setError("");
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Yuklashda xato");
    } finally {
      setLoading(false);
    }
  }, [path]);
  useEffect(() => {
    reload();
  }, [reload]);
  return { data, error, loading, reload, setData };
}

/** Tugma bosilganda amal: busy/xato holati bilan. */
export function useAction() {
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  async function run(fn: () => Promise<unknown>) {
    setBusy(true);
    setError("");
    try {
      await fn();
      return true;
    } catch (e) {
      setError(e instanceof ClientApiError ? e.message : "Xatolik");
      return false;
    } finally {
      setBusy(false);
    }
  }
  return { busy, error, run, setError };
}
