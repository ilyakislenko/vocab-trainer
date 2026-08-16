const DB_NAME = "vocab-trainer-llm-cache";
const STORE = "entries";
const DB_VERSION = 1;

const memory = new Map<string, LlmCacheEntry<unknown>>();

let dbPromise: Promise<IDBDatabase> | null = null;

function openDb(): Promise<IDBDatabase> {
  if (dbPromise) return dbPromise;
  dbPromise = new Promise((resolve, reject) => {
    if (typeof indexedDB === "undefined") {
      reject(new Error("indexedDB unavailable"));
      return;
    }
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains(STORE)) {
        db.createObjectStore(STORE, { keyPath: "key" });
      }
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error ?? new Error("indexedDB open failed"));
  });
  return dbPromise;
}

async function idbGet(key: string): Promise<LlmCacheEntry<unknown> | undefined> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readonly");
    const request = tx.objectStore(STORE).get(key);
    request.onsuccess = () => resolve(request.result as LlmCacheEntry<unknown> | undefined);
    request.onerror = () => reject(request.error ?? new Error("indexedDB get failed"));
  });
}

async function idbSet(key: string, entry: LlmCacheEntry<unknown>): Promise<void> {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE, "readwrite");
    tx.objectStore(STORE).put({ key, ...entry });
    tx.oncomplete = () => resolve();
    tx.onerror = () => reject(tx.error ?? new Error("indexedDB set failed"));
  });
}

export interface LlmCacheEntry<T> {
  value: T;
  expiresAt: number | null;
}

function isExpired(entry: { expiresAt: number | null }): boolean {
  return entry.expiresAt !== null && entry.expiresAt < Date.now();
}

/**
 * Persistent cache for LLM-produced data (word explanations, examples,
 * sentence translations). Uses IndexedDB in browsers and an in-memory store
 * where IndexedDB is unavailable (tests, strict privacy modes). An entry is
 * written once and served until it expires, so previously requested
 * explanations/translations do not hit the language model again.
 */
export const llmCache = {
  async get<T>(key: string): Promise<T | undefined> {
    let idb: LlmCacheEntry<unknown> | undefined;
    try {
      idb = await idbGet(key);
    } catch {
      idb = undefined;
    }
    const entry = idb ?? memory.get(key);
    if (!entry) return undefined;
    if (isExpired(entry)) {
      if (idb) void idbSet(key, entry).catch(() => {});
      else memory.delete(key);
      return undefined;
    }
    if (!idb) memory.set(key, entry);
    return entry.value as T;
  },

  async set<T>(key: string, value: T, ttlMs?: number): Promise<void> {
    const entry: LlmCacheEntry<T> = {
      value,
      expiresAt: ttlMs ? Date.now() + ttlMs : null,
    };
    memory.set(key, entry as LlmCacheEntry<unknown>);
    try {
      await idbSet(key, entry as LlmCacheEntry<unknown>);
    } catch {
      // IndexedDB unavailable — in-memory copy above still serves this session.
    }
  },

  async clear(): Promise<void> {
    memory.clear();
    try {
      const db = await openDb();
      await new Promise<void>((resolve, reject) => {
        const tx = db.transaction(STORE, "readwrite");
        tx.objectStore(STORE).clear();
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error ?? new Error("indexedDB clear failed"));
      });
    } catch {
      // IndexedDB unavailable — nothing to clear beyond memory.
    }
  },
};

/** Helper for caching a network request: read cache first, else fetch and store. */
export async function withLlmCache<T>(
  key: string,
  fetch: () => Promise<T>,
  ttlMs?: number,
): Promise<T> {
  const cached = await llmCache.get<T>(key);
  if (cached !== undefined) return cached;
  const value = await fetch();
  await llmCache.set(key, value, ttlMs);
  return value;
}
