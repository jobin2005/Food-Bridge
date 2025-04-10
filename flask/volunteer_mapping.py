from database import query
from pincode import get_nearby_pincodes

def get_nearby_volunteers_from_ngo(ngo_id):
    # Step 1: Get all donor IDs accepted by this NGO
    donor_id_sql = """
        SELECT DISTINCT donorid
        FROM donation
        WHERE ngo_id = :ngo_id
    """
    donor_id_results = query(donor_id_sql, {'ngo_id': ngo_id})
    donor_ids = [row[0] for row in donor_id_results]
    
    if not donor_ids:
        return []

    # Step 2: Get pincodes of those donors
    bind_vars = {f'id{i}': did for i, did in enumerate(donor_ids)}
    format_ids = ', '.join(f':id{i}' for i in range(len(donor_ids)))

    donor_pincode_sql = f"""
        SELECT DISTINCT a.pincode
        FROM donor d
        JOIN address a ON d.addressid = a.addressid
        WHERE d.id IN ({format_ids})
    """
    donor_pincode_results = query(donor_pincode_sql, bind_vars)
    donor_pincodes = [row[0] for row in donor_pincode_results]

    if not donor_pincodes:
        return []

    # Step 3: Get nearby pincodes for all donor pincodes
    nearby_pincode_set = set()
    for pincode in donor_pincodes:
        nearby_pincode_set.update(get_nearby_pincodes(pincode))

    if not nearby_pincode_set:
        return []

    # Step 4: Get volunteers from these nearby pincodes
    nearby_pincode_list = list(nearby_pincode_set)
    bind_vol_vars = {f'p{i}': p for i, p in enumerate(nearby_pincode_list)}
    format_pins = ', '.join(f':p{i}' for i in range(len(nearby_pincode_list)))

    volunteer_sql = f"""
        SELECT v.id, v.fn || ' ' || v.ln AS name, v.email, v.phone, v.servicearea
        FROM volunteer v
        JOIN address a ON v.addressid = a.addressid
        WHERE a.pincode IN ({format_pins}) AND AVAILABLE = 1
    """
    return query(volunteer_sql, bind_vol_vars)