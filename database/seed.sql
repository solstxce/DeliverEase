-- Create admin user
INSERT INTO de_users (
    id,
    email,
    password_hash,
    user_type,
    full_name,
    phone_number,
    created_at,
    last_login
) VALUES (
    uuid_generate_v4(),
    'admin@deliverease.com',
    'pbkdf2:sha256:600000$dkOzc1zTGgzXxgxp$5aa0b9f86e1d2e62b37f9b7c5b2c8f5d4aa2296b7c123456789abcdef0123456', -- password: admin123
    'admin',
    'Admin User',
    '+1234567890',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Create regular user
INSERT INTO de_users (
    id,
    email,
    password_hash,
    user_type,
    full_name,
    phone_number,
    created_at,
    last_login
) VALUES (
    uuid_generate_v4(),
    'user@deliverease.com',
    'pbkdf2:sha256:600000$dkOzc1zTGgzXxgxp$5aa0b9f86e1d2e62b37f9b7c5b2c8f5d4aa2296b7c123456789abcdef0123456', -- password: user123
    'user',
    'John Doe',
    '+1987654321',
    CURRENT_TIMESTAMP,
    CURRENT_TIMESTAMP
);

-- Create driver user
WITH inserted_driver AS (
    INSERT INTO de_users (
        id,
        email,
        password_hash,
        user_type,
        full_name,
        phone_number,
        created_at,
        last_login
    ) VALUES (
        uuid_generate_v4(),
        'driver@deliverease.com',
        'pbkdf2:sha256:600000$dkOzc1zTGgzXxgxp$5aa0b9f86e1d2e62b37f9b7c5b2c8f5d4aa2296b7c123456789abcdef0123456', -- password: driver123
        'driver',
        'Mike Smith',
        '+1122334455',
        CURRENT_TIMESTAMP,
        CURRENT_TIMESTAMP
    ) RETURNING id
)
-- Add driver details
INSERT INTO de_driver_details (
    id,
    user_id,
    vehicle_type,
    license_number,
    current_location,
    is_available,
    created_at
) VALUES (
    uuid_generate_v4(),
    (SELECT id FROM inserted_driver),
    'Van',
    'DL123456',
    'New York, NY',
    true,
    CURRENT_TIMESTAMP
);

-- Create some sample orders
INSERT INTO de_orders (
    id,
    user_id,
    pickup_location,
    delivery_location,
    item_description,
    weight,
    status,
    created_at,
    price
) VALUES (
    uuid_generate_v4(),
    (SELECT id FROM de_users WHERE email = 'user@deliverease.com'),
    '123 Main St, New York, NY',
    '456 Park Ave, New York, NY',
    'Package containing books',
    2.5,
    'pending',
    CURRENT_TIMESTAMP,
    25.00
);

-- Create a sample support ticket
WITH inserted_ticket AS (
    INSERT INTO de_tickets (
        id,
        user_id,
        subject,
        status,
        created_at
    ) VALUES (
        uuid_generate_v4(),
        (SELECT id FROM de_users WHERE email = 'user@deliverease.com'),
        'Delivery Delay Question',
        'open',
        CURRENT_TIMESTAMP
    ) RETURNING id
)
INSERT INTO de_ticket_messages (
    id,
    ticket_id,
    sender_id,
    message,
    created_at
) VALUES (
    uuid_generate_v4(),
    (SELECT id FROM inserted_ticket),
    (SELECT id FROM de_users WHERE email = 'user@deliverease.com'),
    'When will my package arrive?',
    CURRENT_TIMESTAMP
); 