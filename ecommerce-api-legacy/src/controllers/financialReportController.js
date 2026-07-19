const financialReportService = require('../services/financialReportService');
const AppError = require('../errors/AppError');

function createFinancialReportController({ db }) {
    return async function getFinancialReport(req, res, next) {
        try {
            const report = await financialReportService.buildReport(db);
            res.json(report);
        } catch (err) {
            next(new AppError(500, "Erro DB"));
        }
    };
}

module.exports = createFinancialReportController;
