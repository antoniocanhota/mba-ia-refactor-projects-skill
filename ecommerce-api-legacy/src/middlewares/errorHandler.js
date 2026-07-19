const AppError = require('../errors/AppError');
const logger = require('../utils/logger');

function errorHandler(err, req, res, next) {
    if (err instanceof AppError) {
        return res.status(err.statusCode).send(err.message);
    }

    logger.error(`Erro não tratado em ${req.method} ${req.originalUrl}: ${err.message}`);
    res.status(500).send("Erro interno do servidor");
}

module.exports = errorHandler;
