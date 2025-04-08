from database import query

def get_donors_by_pincode(pincodes):
    if isinstance(pincodes, int):
        pincodes = [pincodes]

    if not pincodes:
        return []  # Avoid executing invalid SQL

    bind_vars = {f'p{i}': pin for i, pin in enumerate(pincodes)}
    format_strings = ', '.join(f':p{i}' for i in range(len(pincodes)))

    sql = f"""
        SELECT d.FN || ' ' || d.LN AS donor_name, f.foodname AS food_name
        FROM donor d
        JOIN donation dn ON d.id = dn.donorid
        JOIN food f ON dn.foodid = f.foodid
        JOIN address a ON d.addressid = a.addressid
        WHERE a.pincode IN ({format_strings})
    """

    return query(sql, bind_vars)
