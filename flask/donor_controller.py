from database import query


def get_donors_by_pincode(pincode_list):
    if not pincode_list:
        return {}

    # Generate Oracle bind variables: :1, :2, ...
    bind_placeholders = ','.join([f':{i+1}' for i in range(len(pincode_list))])
    sql = f"""
        SELECT id, fn || ' ' || ln AS name, pincode
        FROM donor
        WHERE pincode IN ({bind_placeholders})
    """

    try:
        # Unpack the list using * so that it matches :1, :2, ...
        donors = query(sql, params=tuple(pincode_list))

        # Convert results to dictionary grouped by pincode
        donor_dict = {}
        for donor_id, name, pincode in donors:
            donor_info = {
                "id": donor_id,
                "name": name,
                "pincode": pincode
            }
            donor_dict.setdefault(pincode, []).append(donor_info)

        return donor_dict

    except Exception as e:
        print("Error fetching donors by pincode:", str(e))
        return {}
