const express = require('express');
const createCheckoutController = require('../controllers/checkoutController');
const createFinancialReportController = require('../controllers/financialReportController');
const createUserController = require('../controllers/userController');

function createRouter({ db, cache }) {
    const router = express.Router();

    router.post('/api/checkout', createCheckoutController({ db, cache }));
    router.get('/api/admin/financial-report', createFinancialReportController({ db }));
    router.delete('/api/users/:id', createUserController({ db }));

    return router;
}

module.exports = createRouter;
