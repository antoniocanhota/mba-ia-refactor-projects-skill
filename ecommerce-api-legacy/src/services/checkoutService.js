const AppError = require('../errors/AppError');
const courseModel = require('../models/courseModel');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');
const passwordHasher = require('../utils/passwordHasher');
const logger = require('../utils/logger');

function maskCardNumber(cardNumber) {
    const visibleDigits = 4;
    const masked = '*'.repeat(Math.max(cardNumber.length - visibleDigits, 0));
    return `${masked}${cardNumber.slice(-visibleDigits)}`;
}

async function resolveUserId(db, { username, email, password }) {
    let user;
    try {
        user = await userModel.findByEmail(db, email);
    } catch (err) {
        throw new AppError(500, "Erro DB");
    }

    if (user) return user.id;

    const passwordHash = passwordHasher.hash(password || "123456");
    try {
        return await userModel.create(db, { name: username, email, passwordHash });
    } catch (err) {
        throw new AppError(500, "Erro ao criar usuário");
    }
}

async function checkout(db, cache, { username, email, password, courseId, cardNumber }) {
    let course;
    try {
        course = await courseModel.findActiveById(db, courseId);
    } catch (err) {
        throw new AppError(500, "Erro DB");
    }
    if (!course) {
        throw new AppError(404, "Curso não encontrado");
    }

    const userId = await resolveUserId(db, { username, email, password });

    logger.info(`Processando cartão ${maskCardNumber(cardNumber)}`);
    const status = cardNumber.startsWith("4") ? "PAID" : "DENIED";
    if (status === "DENIED") {
        throw new AppError(400, "Pagamento recusado");
    }

    let enrollmentId;
    try {
        enrollmentId = await enrollmentModel.create(db, { userId, courseId });
    } catch (err) {
        throw new AppError(500, "Erro Matrícula");
    }

    try {
        await paymentModel.create(db, { enrollmentId, amount: course.price, status });
    } catch (err) {
        throw new AppError(500, "Erro Pagamento");
    }

    try {
        await auditLogModel.create(db, `Checkout curso ${courseId} por ${userId}`);
    } catch (err) {
        logger.warn(`Falha ao registrar audit log do checkout: ${err.message}`);
    }

    cache.set(`last_checkout_${userId}`, course.title);
    logger.info(`Cache atualizado para last_checkout_${userId}`);

    return { message: "Sucesso", enrollmentId };
}

module.exports = { checkout };
