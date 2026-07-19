const { get, run } = require('../db/dbHelpers');

function findByEmail(db, email) {
    return get(db, "SELECT * FROM users WHERE email = ?", [email]);
}

function findById(db, id) {
    return get(db, "SELECT name, email FROM users WHERE id = ?", [id]);
}

async function create(db, { name, email, passwordHash }) {
    const result = await run(db, "INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, passwordHash]);
    return result.lastID;
}

function deleteById(db, id) {
    return run(db, "DELETE FROM users WHERE id = ?", [id]);
}

module.exports = { findByEmail, findById, create, deleteById };
