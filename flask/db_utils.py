from database import query

def get_ngo_pincode(user_id):
    sql = """
        SELECT a.pincode
        FROM ngo n
        JOIN address a ON n.addressid = a.addressid
        WHERE n.id = :user_id
    """
    result = query(sql, {'user_id': user_id})
    return result[0][0] if result else None






