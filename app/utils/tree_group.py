from app.models.group_info import GroupInfo

def build_group_tree(raw_list, parent_id=0):
    """递归生成前端layui树形结构"""
    tree = []
    for item in raw_list:
        if item.parent_id == parent_id:
            child_nodes = build_group_tree(raw_list, item.id)
            node = {
                "id": item.id,
                "title": item.group_name,
                "children": child_nodes if child_nodes else None
            }
            tree.append(node)
    return tree

def get_child_group_ids(root_id: int) -> list:
    """递归获取当前分组+所有下级子分组ID（用于权限过滤）"""
    ids = [root_id]
    child_list = GroupInfo.query.filter_by(parent_id=root_id).all()
    for child in child_list:
        ids.extend(get_child_group_ids(child.id))
    return ids

def get_all_group_flat():
    """获取全部平铺分组列表"""
    return GroupInfo.query.order_by(GroupInfo.parent_id, GroupInfo.id).all()