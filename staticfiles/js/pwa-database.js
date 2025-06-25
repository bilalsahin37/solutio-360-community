/**
 * Solutio 360 - PWA IndexedDB Database Manager
 * Offline veri depolama ve senkronizasyon sistemi
 */

class PWADatabase {
    constructor() {
        this.dbName = 'Solutio360DB';
        this.dbVersion = 1;
        this.db = null;
        this.stores = {
            complaints: 'complaints',
            reports: 'reports',
            users: 'users',
            sync_queue: 'sync_queue',
            cache: 'cache'
        };
        
        this.init();
    }
    
    /**
     * Database'i başlatır
     */
    async init() {
        try {
            this.db = await this.openDatabase();
            console.log('[PWA-DB] Database başarıyla açıldı');
        } catch (error) {
            console.error('[PWA-DB] Database açma hatası:', error);
        }
    }
    
    /**
     * IndexedDB bağlantısını açar
     */
    openDatabase() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open(this.dbName, this.dbVersion);
            
            request.onerror = () => {
                reject(new Error('Database açılamadı'));
            };
            
            request.onsuccess = (event) => {
                resolve(event.target.result);
            };
            
            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                
                // Complaints store
                if (!db.objectStoreNames.contains(this.stores.complaints)) {
                    const complaintsStore = db.createObjectStore(this.stores.complaints, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    complaintsStore.createIndex('status', 'status', { unique: false });
                    complaintsStore.createIndex('created_at', 'created_at', { unique: false });
                    complaintsStore.createIndex('user_id', 'user_id', { unique: false });
                }
                
                // Reports store
                if (!db.objectStoreNames.contains(this.stores.reports)) {
                    const reportsStore = db.createObjectStore(this.stores.reports, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    reportsStore.createIndex('type', 'type', { unique: false });
                    reportsStore.createIndex('created_at', 'created_at', { unique: false });
                }
                
                // Users store
                if (!db.objectStoreNames.contains(this.stores.users)) {
                    const usersStore = db.createObjectStore(this.stores.users, {
                        keyPath: 'id'
                    });
                    usersStore.createIndex('email', 'email', { unique: true });
                }
                
                // Sync queue store
                if (!db.objectStoreNames.contains(this.stores.sync_queue)) {
                    const syncStore = db.createObjectStore(this.stores.sync_queue, {
                        keyPath: 'id',
                        autoIncrement: true
                    });
                    syncStore.createIndex('action', 'action', { unique: false });
                    syncStore.createIndex('timestamp', 'timestamp', { unique: false });
                    syncStore.createIndex('synced', 'synced', { unique: false });
                }
                
                // Cache store
                if (!db.objectStoreNames.contains(this.stores.cache)) {
                    const cacheStore = db.createObjectStore(this.stores.cache, {
                        keyPath: 'key'
                    });
                    cacheStore.createIndex('expiry', 'expiry', { unique: false });
                }
                
                console.log('[PWA-DB] Database şeması oluşturuldu');
            };
        });
    }
    
    /**
     * Veri ekler
     */
    async add(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            // Timestamp ekle
            data.created_at = data.created_at || new Date().toISOString();
            data.updated_at = new Date().toISOString();
            
            const request = store.add(data);
            
            request.onsuccess = () => {
                console.log(`[PWA-DB] ${storeName} verisine eklendi:`, data);
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error(`[PWA-DB] ${storeName} ekleme hatası:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * Veri günceller
     */
    async update(storeName, data) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            
            // Update timestamp
            data.updated_at = new Date().toISOString();
            
            const request = store.put(data);
            
            request.onsuccess = () => {
                console.log(`[PWA-DB] ${storeName} verisi güncellendi:`, data);
                resolve(request.result);
            };
            
            request.onerror = () => {
                console.error(`[PWA-DB] ${storeName} güncelleme hatası:`, request.error);
                reject(request.error);
            };
        });
    }
    
    /**
     * ID'ye göre veri getirir
     */
    async get(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            const request = store.get(id);
            
            request.onsuccess = () => {
                resolve(request.result);
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    
    /**
     * Tüm verileri getirir
     */
    async getAll(storeName, indexName = null, query = null) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readonly');
            const store = transaction.objectStore(storeName);
            
            let request;
            if (indexName && query) {
                const index = store.index(indexName);
                request = index.getAll(query);
            } else {
                request = store.getAll();
            }
            
            request.onsuccess = () => {
                resolve(request.result);
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    
    /**
     * Veri siler
     */
    async delete(storeName, id) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.delete(id);
            
            request.onsuccess = () => {
                console.log(`[PWA-DB] ${storeName} verisi silindi: ${id}`);
                resolve(request.result);
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    
    /**
     * Store'u temizler
     */
    async clear(storeName) {
        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction([storeName], 'readwrite');
            const store = transaction.objectStore(storeName);
            const request = store.clear();
            
            request.onsuccess = () => {
                console.log(`[PWA-DB] ${storeName} store temizlendi`);
                resolve(request.result);
            };
            
            request.onerror = () => {
                reject(request.error);
            };
        });
    }
    
    /**
     * Şikayet ekler (offline)
     */
    async addComplaint(complaintData) {
        try {
            // Offline flag ekle
            complaintData.is_offline = true;
            complaintData.sync_status = 'pending';
            
            // Şikayeti offline store'a ekle
            const result = await this.add(this.stores.complaints, complaintData);
            
            // Sync queue'ya ekle
            await this.addToSyncQueue('CREATE', 'complaints', complaintData, result);
            
            return result;
        } catch (error) {
            console.error('[PWA-DB] Offline şikayet ekleme hatası:', error);
            throw error;
        }
    }
    
    /**
     * Rapor ekler (offline)
     */
    async addReport(reportData) {
        try {
            reportData.is_offline = true;
            reportData.sync_status = 'pending';
            
            const result = await this.add(this.stores.reports, reportData);
            await this.addToSyncQueue('CREATE', 'reports', reportData, result);
            
            return result;
        } catch (error) {
            console.error('[PWA-DB] Offline rapor ekleme hatası:', error);
            throw error;
        }
    }
    
    /**
     * Sync queue'ya işlem ekler
     */
    async addToSyncQueue(action, model, data, localId = null) {
        const syncData = {
            action: action, // CREATE, UPDATE, DELETE
            model: model,
            data: data,
            local_id: localId,
            timestamp: new Date().toISOString(),
            synced: false,
            retry_count: 0,
            max_retries: 3
        };
        
        return await this.add(this.stores.sync_queue, syncData);
    }
    
    /**
     * Sync bekleyen işlemleri getirir
     */
    async getPendingSyncOperations() {
        return await this.getAll(this.stores.sync_queue, 'synced', false);
    }
    
    /**
     * Sync işlemini tamamlandı olarak işaretler
     */
    async markSyncCompleted(syncId, serverId = null) {
        const syncData = await this.get(this.stores.sync_queue, syncId);
        if (syncData) {
            syncData.synced = true;
            syncData.server_id = serverId;
            syncData.synced_at = new Date().toISOString();
            await this.update(this.stores.sync_queue, syncData);
        }
    }
    
    /**
     * Cache verisini saklar
     */
    async setCache(key, data, ttl = 3600000) { // Default 1 saat
        const cacheData = {
            key: key,
            data: data,
            expiry: new Date(Date.now() + ttl).toISOString(),
            created_at: new Date().toISOString()
        };
        
        return await this.update(this.stores.cache, cacheData);
    }
    
    /**
     * Cache verisini getirir
     */
    async getCache(key) {
        try {
            const cacheData = await this.get(this.stores.cache, key);
            
            if (!cacheData) {
                return null;
            }
            
            // Expiry kontrolü
            const now = new Date();
            const expiry = new Date(cacheData.expiry);
            
            if (now > expiry) {
                await this.delete(this.stores.cache, key);
                return null;
            }
            
            return cacheData.data;
        } catch (error) {
            console.error('[PWA-DB] Cache getirme hatası:', error);
            return null;
        }
    }
    
    /**
     * Süresi geçmiş cache'leri temizler
     */
    async cleanExpiredCache() {
        try {
            const allCache = await this.getAll(this.stores.cache);
            const now = new Date();
            
            for (const cache of allCache) {
                const expiry = new Date(cache.expiry);
                if (now > expiry) {
                    await this.delete(this.stores.cache, cache.key);
                }
            }
            
            console.log('[PWA-DB] Süresi geçmiş cache temizlendi');
        } catch (error) {
            console.error('[PWA-DB] Cache temizleme hatası:', error);
        }
    }
    
    /**
     * Database istatistiklerini getirir
     */
    async getStats() {
        try {
            const stats = {};
            
            for (const [name, storeName] of Object.entries(this.stores)) {
                const count = (await this.getAll(storeName)).length;
                stats[name] = count;
            }
            
            return stats;
        } catch (error) {
            console.error('[PWA-DB] İstatistik hatası:', error);
            return {};
        }
    }
}

// Global instance
window.pwaDB = new PWADatabase();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = PWADatabase;
}

console.log('[PWA-DB] Database manager yüklendi'); 