const { get, all } = require('../db/dbHelpers');

function findActiveById(db, id) {
    return get(db, "SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
}

function findAll(db) {
    return all(db, "SELECT * FROM courses", []);
}

module.exports = { findActiveById, findAll };
