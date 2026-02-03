INSERT INTO users (email, password_hash, name, role, hero_video_url)
VALUES
  ('admin@abagency.com', 'scrypt:32768:8:1$SavUGdbbHXArwFyo$3a6863c1f45b34d20d7231d8ff16f0993ebb98c600fd72db92e3ea3d07f7f6dc14740afac0902914e8642436ab72305b0baf5b4b3441e14ff4c695cc09d338a6', 'AB AGENCY Admin', 'admin', 'https://www.youtube-nocookie.com/embed/_4FGVRpNoEs'),
  ('moderator@abagency.com', 'scrypt:32768:8:1$WKDMhYpiiraqJ8b9$5f866ed4e6697de93c03aacb9a016e12917845b69630f98fc3779d31a6af2a398641c88eab8755a197b3398089ca35dec3543f59c639e53b25d6490bc6ef2fb3', 'AB AGENCY Moderator', 'moderator', 'https://www.youtube-nocookie.com/embed/Tz-khkZz_zY'),
  ('artist@abagency.com', 'scrypt:32768:8:1$4rPFHru41ddP0xp5$062236ce3abd185654c8e519b4985d3703d5e112bf42debb4a7132bb7993043e7e75ec41c10488e3f261361863c718c2d62a27a443c74dbbff2b1c5fb46749d5', 'Artiste Résident', 'community', 'https://www.youtube-nocookie.com/embed/7FhkTtoq9Pg');

INSERT INTO profiles (user_id, bio, location, phone, website)
VALUES
  (1, 'Administrateur de la plateforme AB AGENCY.', 'Paris, FR', '+33 1 23 45 67 89', 'https://abagency.com'),
  (2, 'Modérateur en charge des échanges communautaires.', 'Lyon, FR', '+33 4 56 78 90 12', NULL),
  (3, 'Artiste spécialisé en performances scéniques.', 'Marseille, FR', '+33 6 11 22 33 44', 'https://portfolio.example');

INSERT INTO events (user_id, title, event_date, location)
VALUES
  (3, 'Showcase privé', CURRENT_DATE + INTERVAL '7 days', 'Performance privée pour un client.'),
  (3, 'Festival urbain', CURRENT_DATE + INTERVAL '21 days', 'Participation au festival annuel.');

INSERT INTO media_assets (user_id, media_type, url)
VALUES
  (3, 'video', 'https://www.youtube.com/embed/_4FGVRpNoEs'),
  (3, 'image', 'https://via.placeholder.com/800x500.png?text=AB+Agency');

INSERT INTO performances (user_id, title, performance_date, fee)
VALUES
  (3, 'Gala d\'hiver', CURRENT_DATE - INTERVAL '30 days', 1200.00),
  (3, 'Soirée corporate', CURRENT_DATE - INTERVAL '12 days', 800.00);

INSERT INTO subscriptions (user_id, plan, status, renewal_date)
VALUES
  (3, 'Pro', 'active', CURRENT_DATE + INTERVAL '30 days');

INSERT INTO messages (sender_id, recipient_id, body)
VALUES
  (3, 2, 'Bonjour, j\'ai une question sur la prochaine programmation.'),
  (2, 3, 'Merci ! Je reviens vers toi très vite.');
