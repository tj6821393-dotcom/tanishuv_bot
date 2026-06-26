CREATE_TABLES = """

CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    unique_id VARCHAR(20) UNIQUE NOT NULL,
    full_name VARCHAR(100) NOT NULL,
    gender VARCHAR(10) NOT NULL,
    age INTEGER NOT NULL,
    city VARCHAR(100) NOT NULL,
    bio TEXT,
    goal VARCHAR(50),
    interests TEXT,
    photos TEXT,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    balance INTEGER DEFAULT 0,
    tariff VARCHAR(20) DEFAULT 'free',
    tariff_until TIMESTAMP,
    like_count INTEGER DEFAULT 0,
    like_reset_at TIMESTAMP,
    is_hidden BOOLEAN DEFAULT FALSE,
    is_verified BOOLEAN DEFAULT FALSE,
    is_blocked BOOLEAN DEFAULT FALSE,
    story_file_id TEXT,
    story_until TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS likes (
    id SERIAL PRIMARY KEY,
    from_user BIGINT NOT NULL,
    to_user BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(from_user, to_user)
);

CREATE TABLE IF NOT EXISTS matches (
    id SERIAL PRIMARY KEY,
    user1 BIGINT NOT NULL,
    user2 BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user1, user2)
);

CREATE TABLE IF NOT EXISTS cards (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    text TEXT NOT NULL,
    emoji VARCHAR(10),
    price INTEGER NOT NULL,
    card_type VARCHAR(50) NOT NULL
);

CREATE TABLE IF NOT EXISTS user_cards (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    card_id INTEGER NOT NULL,
    quantity INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    from_user BIGINT NOT NULL,
    to_user BIGINT NOT NULL,
    text TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    text TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS location_perms (
    id SERIAL PRIMARY KEY,
    from_user BIGINT NOT NULL,
    to_user BIGINT NOT NULL,
    perm_type VARCHAR(20) NOT NULL,
    expires_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(from_user, to_user)
);

CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT NOT NULL,
    amount INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    check_file_id TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS complaints (
    id SERIAL PRIMARY KEY,
    from_user BIGINT NOT NULL,
    to_user BIGINT NOT NULL,
    reason TEXT,
    status VARCHAR(20) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT NOW()
);

INSERT INTO cards (name, text, emoji, price, card_type) VALUES
('Oddiy tanishuv', 'Salom! Profilingizni ko''rib qoldim, siz bilan tanishib qolsam deb o''yladim. Agar qarshi bo''lmasangiz, javob bering.', '💌', 10000, 'simple'),
('Jiddiy tanishuv', 'Salom! Siz bilan tanishmoqchi edim. Men jiddiy munosabat izlayapman va siz menga mos ko''rindingiz. Imkoningiz bo''lsa javob bering.', '💖', 10000, 'serious'),
('Oila qurish niyati', 'Assalomu alaykum! Men hayotimni birga quradigan insonni izlayapman. Agar siz ham shu yo''lda bo''lsangiz, tanishib olsak deb o''yladim.', '💍', 10000, 'family'),
('Lokatsiya so''rovi', 'Siz bilan yaqinroq bo''lishni istayman. Taxminiy joylashuvingizni ko''rishga ruxsat berasizmi?', '📍', 25000, 'location')
ON CONFLICT DO NOTHING;
"""

async def create_tables(pool):
    async with pool.acquire() as conn:
        await conn.execute(CREATE_TABLES)