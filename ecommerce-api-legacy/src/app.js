const express = require('express');
const config = require('./config/config');
const logger = require('./utils/logger');
const { createConnection, initSchema } = require('./db/connection');
const InMemoryCache = require('./cache/inMemoryCache');
const createRouter = require('./routes');
const errorHandler = require('./middlewares/errorHandler');

async function start() {
    const app = express();
    app.use(express.json());

    const db = createConnection();
    await initSchema(db);

    const cache = new InMemoryCache();

    app.use(createRouter({ db, cache }));
    app.use(errorHandler);

    app.listen(config.port, () => {
        logger.info(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}

start();

module.exports = { start };
