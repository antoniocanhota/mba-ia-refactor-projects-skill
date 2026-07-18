const express = require('express');
const AppManager = require('./AppManager');
const { config } = require('./utils');
const { configure: configureLogger } = require('./logger');

// Configuração central do logger, uma única vez, no ponto de entrada da aplicação.
configureLogger({ level: process.env.LOG_LEVEL || 'info' });

const app = express();
app.use(express.json());

const manager = new AppManager();
manager.initDb();
manager.setupRoutes(app);

app.listen(config.port, () => {
    // Banner de inicialização (UX de boot da aplicação), não é log de runtime — preservado.
    console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
});
