import { api } from '../utils/request'

/** 帖子列表 */
export function fetchPosts(params) {
  return api.get('/posts', params)
}

/** 帖子详情 */
export function fetchPostDetail(id) {
  return api.get(`/posts/${id}`)
}

/** 创建帖子 */
export function createPost(data) {
  return api.post('/posts', data)
}

/** 编辑帖子 */
export function updatePost(id, data) {
  return api.put(`/posts/${id}`, data)
}

/** 删除帖子 */
export function deletePost(id) {
  return api.delete(`/posts/${id}`)
}

/** 点赞/取消点赞 */
export function toggleLike(id) {
  return api.post(`/posts/${id}/like`)
}

/** 收藏/取消收藏 */
export function toggleCollect(id, folderName) {
  return api.post(`/posts/${id}/collect`, { folder_name: folderName })
}

/** 转发帖子 */
export function sharePost(id, shareType, comment) {
  return api.post(`/posts/${id}/share`, { share_type: shareType, comment })
}

/** 参与投票 */
export function voteOnPost(id, optionIds) {
  return api.post(`/posts/${id}/vote`, { option_ids: optionIds })
}

/** 板块列表 */
export function fetchCategories() {
  return api.get('/categories')
}

/** 收藏列表 */
export function fetchCollections(params) {
  return api.get('/users/me/collections', params)
}
