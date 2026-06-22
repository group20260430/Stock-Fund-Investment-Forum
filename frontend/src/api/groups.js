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

/** 退出群组 */
export function leaveGroup(groupId) {
  return api.post(`/groups/${groupId}/leave`)
}

/** 审核群组成员（支持 approve/reject） */
export function reviewGroupMember(groupId, data) {
  return api.post(`/groups/${groupId}/members/approve`, data)
}

/** 审核群组成员（兼容，仅 approve） */
export function approveGroupMember(groupId, userId) {
  return api.post(`/groups/${groupId}/members/${userId}/approve`)
}

/** 移出群组成员 */
export function removeGroupMember(groupId, userId) {
  return api.delete(`/groups/${groupId}/members/${userId}`)
}

/** 解散群组 */
export function deleteGroup(groupId) {
  return api.delete(`/groups/${groupId}`)
}

/** 编辑群组信息 */
export function updateGroup(groupId, data) {
  return api.put(`/groups/${groupId}`, data)
}

/** 在群组内发帖 */
export function createGroupPost(groupId, data) {
  return api.post(`/groups/${groupId}/posts`, data)
}

/** 群组帖子列表 */
export function fetchGroupPosts(groupId, params) {
  return api.get(`/groups/${groupId}/posts`, params)
}
