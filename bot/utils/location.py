from bot.utils.matching import calculate_distance

def get_distance_text(lat1, lon1, lat2, lon2) -> str:
    if not all([lat1, lon1, lat2, lon2]):
        return "Noma'lum"
    dist = calculate_distance(lat1, lon1, lat2, lon2)
    if dist < 1:
        return f"{int(dist * 1000)} m"
    return f"{dist:.1f} km"