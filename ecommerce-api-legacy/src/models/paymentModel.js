const { run, get } = require('../db/dbHelpers');

async function create(db, { enrollmentId, amount, status }) {
    const result = await run(db, "INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)", [enrollmentId, amount, status]);
    return result.lastID;
}

function findByEnrollmentId(db, enrollmentId) {
    return get(db, "SELECT amount, status FROM payments WHERE enrollment_id = ?", [enrollmentId]);
}

module.exports = { create, findByEnrollmentId };
