import { api } from '../utils/request'

/** 全文搜索 */
export function search(params) {
  return api.get('/search', params)
}

/** 搜索联想 */
export function searchSuggestions(keyword, type = 'all') {
  return api.get('/search/suggestions', { keyword, type })
}

/** 搜索页推荐 */
export function searchRecommendations() {
  return api.get('/search/recommendations')
}
