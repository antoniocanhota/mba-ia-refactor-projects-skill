const checkoutService = require('../services/checkoutService');
const AppError = require('../errors/AppError');

function createCheckoutController({ db, cache }) {
    return async function checkout(req, res, next) {
        const { usr: username, eml: email, pwd: password, c_id: courseId, card: cardNumber } = req.body;

        if (!username || !email || !courseId || !cardNumber) {
            return next(new AppError(400, "Bad Request"));
        }

        try {
            const result = await checkoutService.checkout(db, cache, { username, email, password, courseId, cardNumber });
            res.status(200).json({ msg: result.message, enrollment_id: result.enrollmentId });
        } catch (err) {
            next(err);
        }
    };
}

module.exports = createCheckoutController;
