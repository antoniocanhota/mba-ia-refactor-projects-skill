class InMemoryCache {
    constructor() {
        this.store = new Map();
    }

    set(key, value) {
        this.store.set(key, value);
    }

    get(key) {
        return this.store.get(key);
    }
}

module.exports = InMemoryCache;
