import math

def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_match(user1: dict, user2: dict) -> int:
    score = 0

    # Masofa (30%)
    if user1.get('latitude') and user2.get('latitude'):
        dist = calculate_distance(
            user1['latitude'], user1['longitude'],
            user2['latitude'], user2['longitude']
        )
        if dist <= 2: score += 30
        elif dist <= 5: score += 25
        elif dist <= 10: score += 20
        elif dist <= 20: score += 15
        elif dist <= 50: score += 10
        else: score += 5

    # Qiziqishlar (30%)
    if user1.get('interests') and user2.get('interests'):
        i1 = set(user1['interests'].split(', '))
        i2 = set(user2['interests'].split(', '))
        common = len(i1 & i2)
        total = len(i1 | i2)
        if total > 0:
            score += int((common / total) * 30)

    # Maqsad (25%)
    if user1.get('goal') and user2.get('goal'):
        if user1['goal'] == user2['goal']:
            score += 25
        else:
            score += 10

    # Profil sifati (15%)
    quality = 0
    if user2.get('photos'): quality += 5
    if user2.get('bio'): quality += 5
    if user2.get('interests'): quality += 3
    if user2.get('is_verified'): quality += 2
    score += quality

    return min(score, 100)