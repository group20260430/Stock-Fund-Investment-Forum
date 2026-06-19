import { api } from '../utils/request'

/** 群组列表 */
export function fetchGroups(params) {
  return api.get('/groups', params)
}

/** 创建群组 */
export function createGroup(data) {
  return api.post('/groups', data)
}

/** 加入群组 */
export function joinGroup(groupId) {
  return api.post(`/groups/${groupId}/join`)
}

/** 审核群组成员 */
export function approveGroupMember(groupId, userId) {
  return api.post(`/groups/${groupId}/members/${userId}/approve`)
}

/** 在群组内发帖 */
export function createGroupPost(groupId, data) {
  return api.post(`/groups/${groupId}/posts`, data)
}
