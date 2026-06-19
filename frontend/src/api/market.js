import { api } from '../utils/request'

/**
 * 获取实时指数行情
 * @param {string} secids - 证券 ID，逗号分隔
 */
export function fetchIndices(secids) {
  return api.get('/market/indices', secids ? { secids } : undefined)
}

/**
 * 获取 K 线数据（用于迷你走势图）
 * @param {string} secid - 证券 ID，如 1.000001
 * @param {number} klt    - K线类型：101=日线
 * @param {number} lmt    - 数据条数
 */
export function fetchKline(secid, klt = 101, lmt = 20) {
  return api.get(`/market/kline/${secid}`, { klt, lmt })
}
