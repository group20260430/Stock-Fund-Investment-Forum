import { api } from '../utils/request'

/** 获取评论列表 */
export function fetchComments(postId, params) {
  return api.get(`/posts/${postId}/comments`, params)
}

/** 发表评论 */
export function createComment(postId, data) {
  return api.post(`/posts/${postId}/comments`, data)
}

/** 删除评论 */
export function deleteComment(id) {
  return api.delete(`/comments/${id}`)
}

/** 点赞评论 */
export function likeComment(id) {
  return api.post(`/comments/${id}/like`)
}
