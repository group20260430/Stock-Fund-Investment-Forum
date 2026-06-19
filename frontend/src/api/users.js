import { api } from '../utils/request'

/** 用户资料 */
export function fetchUserProfile(id) {
  return api.get(`/users/${id}`)
}

/** 关注/取消关注 */
export function toggleFollow(userId) {
  return api.post(`/users/${userId}/follow`)
}

/** 粉丝列表 */
export function fetchFollowers(userId, params) {
  return api.get(`/users/${userId}/followers`, params)
}

/** 关注列表 */
export function fetchFollowing(userId, params) {
  return api.get(`/users/${userId}/following`, params)
}

/** 设置星标用户 */
export function setStarred(userId, isStarred) {
  return api.put('/users/me/starred', { user_id: userId, is_starred: isStarred })
}
