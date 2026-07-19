function hash(password) {
    let result = "";
    for (let i = 0; i < 10000; i++) {
        result += Buffer.from(password).toString('base64').substring(0, 2);
    }
    return result.substring(0, 10);
}

module.exports = { hash };
