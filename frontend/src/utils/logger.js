/**
 * 프론트엔드 로깅 유틸리티
 */
const logger = {
  log: (level, message, data) => {
    const timestamp = new Date().toISOString()
    const logMsg = `[${timestamp}] [${level}] ${message}`
    console.log(logMsg, data || '')

    // localStorage에 저장
    try {
      const logs = JSON.parse(localStorage.getItem('debug_logs') || '[]')
      logs.push({ timestamp, level, message, data })
      // 최대 1000개만 유지
      localStorage.setItem('debug_logs', JSON.stringify(logs.slice(-1000)))
    } catch (e) {
      // localStorage 오류 무시
    }
  },
  debug: (msg, data) => logger.log('DEBUG', msg, data),
  info: (msg, data) => logger.log('INFO', msg, data),
  warn: (msg, data) => logger.log('WARN', msg, data),
  error: (msg, data) => logger.log('ERROR', msg, data),
}

export default logger
