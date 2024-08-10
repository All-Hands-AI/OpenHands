const ENTITY_NAME = "UnsavedFileContent";
const DB_VERSION = 1;

function openDb(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(ENTITY_NAME, DB_VERSION);
    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);
    request.onupgradeneeded = () => {
      const db = request.result;
      const needsSaveStore = db.createObjectStore(ENTITY_NAME, {
        keyPath: "key",
      });
      needsSaveStore.createIndex("key", "key", { unique: true });
    };
  });
}

async function getObjectStore(): Promise<IDBObjectStore> {
  const db = await openDb();
  const transaction = db.transaction([ENTITY_NAME], "readwrite");
  return transaction.objectStore(ENTITY_NAME);
}

export function upsertUnsavedFileContent(
  key: string,
  content: string,
): Promise<string> {
  return new Promise((resolve, reject) => {
    getObjectStore().then((objectStore) => {
      const request = objectStore.add({ key, content });
      request.onerror = reject;
      request.onsuccess = () => resolve(key);
    }, reject);
  });
}

export function listUnsavedFileNames(): Promise<string[]> {
  return new Promise((resolve, reject) => {
    getObjectStore().then((objectStore) => {
      const unsavedFileNames: string[] = [];
      const request = objectStore.openCursor();
      request.onerror = reject;
      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          unsavedFileNames.push(cursor.value.key);
          cursor.continue();
        } else {
          resolve(unsavedFileNames);
        }
      };
    });
  });
}

export function deleteUnsavedFileContent(key: string): Promise<boolean> {
  return new Promise((resolve, reject) => {
    getObjectStore().then((objectStore) => {
      const request = objectStore.delete(key);
      request.onerror = () => resolve(false);
      request.onsuccess = () => resolve(true);
    }, reject);
  });
}

export function deleteAllUnsavedFileContent(): Promise<void> {
  return new Promise((resolve, reject) => {
    getObjectStore().then((objectStore) => {
      const request = objectStore.openCursor();
      request.onerror = reject;
      request.onsuccess = () => {
        const cursor = request.result;
        if (cursor) {
          cursor.delete();
          cursor.continue();
        } else {
          resolve();
        }
      };
    }, reject);
  });
}

export function getUnsavedFileContent(key: string): Promise<string | null> {
  return new Promise((resolve, reject) => {
    getObjectStore().then((objectStore) => {
      const request = objectStore.get(key);
      request.onerror = () => resolve(null);
      request.onsuccess = () => {
        const { content } = request.result;
        resolve(content);
      };
    }, reject);
  });
}
