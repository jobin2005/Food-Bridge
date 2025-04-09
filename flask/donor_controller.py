from database import query

def get_donors_by_pincode(pincodes):
    if isinstance(pincodes, int):
        pincodes = [pincodes]

    if not pincodes:
        return []  # Avoid executing invalid SQL

    bind_vars = {f'p{i}': pin for i, pin in enumerate(pincodes)}
    format_strings = ', '.join(f':p{i}' for i in range(len(pincodes)))

    sql = f"""
        SELECT 
            d.FN || ' ' || d.LN AS donor_name,
            f.foodname AS food_name,
            dn.donationid,
            dn.ngo_id
        FROM donor d
        JOIN donation dn ON d.id = dn.donorid
        JOIN food f ON dn.foodid = f.foodid
        JOIN address a ON d.addressid = a.addressid
        WHERE a.pincode IN ({format_strings})
        AND dn.ngo_id IS NULL
    """

    results = query(sql, bind_vars)

    donor_food_data = [
        {
            'donor_name': row[0],
            'food_name': row[1],
            'donation_id': row[2],
            'ngo_id': row[3]  # not status anymore
        }
        for row in results
    ]

    return donor_food_data
