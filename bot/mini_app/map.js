const tg = window.Telegram.WebApp;
tg.expand();

const BOT_API = "https://your-railway-url.up.railway.app";

ymaps.ready(async function () {
    const map = new ymaps.Map("map", {
        center: [41.2995, 69.2401],
        zoom: 13
    });

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(async (pos) => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            map.setCenter([lat, lon], 14);

            const res = await fetch(`${BOT_API}/users/nearby?lat=${lat}&lon=${lon}`);
            const users = await res.json();

            users.forEach(user => {
                const placemark = new ymaps.Placemark(
                    [user.latitude, user.longitude],
                    {
                        balloonContentHeader: user.full_name,
                        balloonContentBody: `
                            <img src="${user.photo}" width="80" style="border-radius:50%"><br>
                            <b>${user.full_name}</b>, ${user.age} yosh<br>
                            📍 ${user.city}<br>
                            ❤️ ${user.interests}
                        `,
                    },
                    { preset: 'islands#redDotIcon' }
                );
                map.geoObjects.add(placemark);
            });
        });
    }
});