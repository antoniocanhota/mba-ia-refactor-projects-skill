// Logger estruturado mínimo com níveis, timestamp e origem configurável.
// Substitui console.log/console.error usados como mecanismo de logging de runtime.
// Nível configurável via variável de ambiente LOG_LEVEL (default: "info").

const LEVELS = { error: 0, warn: 1, info: 2, debug: 3 };

let currentLevel = 'info';

function configure({ level } = {}) {
    if (level && Object.prototype.hasOwnProperty.call(LEVELS, level)) {
        currentLevel = level;
    }
}

function createLogger(name) {
    function write(level, message) {
        if (LEVELS[level] > LEVELS[currentLevel]) return;

        const line = `${new Date().toISOString()} ${level.toUpperCase()} [${name}]: ${message}`;
        if (level === 'error') {
            console.error(line);
        } else {
            console.log(line);
        }
    }

    return {
        error: (message) => write('error', message),
        warn: (message) => write('warn', message),
        info: (message) => write('info', message),
        debug: (message) => write('debug', message),
    };
}

module.exports = { configure, createLogger };
