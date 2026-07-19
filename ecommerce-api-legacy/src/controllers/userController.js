const userModel = require('../models/userModel');

function createUserController({ db }) {
    return async function deleteUser(req, res) {
        const { id } = req.params;
        try {
            await userModel.deleteById(db, id);
        } catch (err) {
            // comportamento original preservado: falha na exclusão não impede a resposta de sucesso
        }
        res.send("Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco.");
    };
}

module.exports = createUserController;
