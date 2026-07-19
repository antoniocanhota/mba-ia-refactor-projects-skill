const { run, all } = require('../db/dbHelpers');

async function create(db, { userId, courseId }) {
    const result = await run(db, "INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)", [userId, courseId]);
    return result.lastID;
}

function findByCourseId(db, courseId) {
    return all(db, "SELECT * FROM enrollments WHERE course_id = ?", [courseId]);
}

module.exports = { create, findByCourseId };
