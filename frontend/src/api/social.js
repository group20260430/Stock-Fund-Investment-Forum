import { api } from '../utils/request'

/** 获取个性化 Feed */
export function fetchFeed(params) {
  return api.get('/feed', params)
}

/** 获取热榜 */
export function fetchHot(params) {
  return api.get('/hot', params)
}
