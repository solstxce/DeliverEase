-- First, add driver_id column to de_orders if it doesn't exist
ALTER TABLE de_orders 
    ADD COLUMN IF NOT EXISTS driver_id UUID REFERENCES de_users(id);

-- Drop existing foreign key constraints if they exist
ALTER TABLE de_orders 
    DROP CONSTRAINT IF EXISTS de_orders_user_id_fkey;

-- Add back the foreign key constraints with explicit names
ALTER TABLE de_orders
    ADD CONSTRAINT de_orders_user_id_fkey 
    FOREIGN KEY (user_id) 
    REFERENCES de_users(id);

-- Add indexes for better performance
CREATE INDEX IF NOT EXISTS idx_orders_user_id 
    ON de_orders(user_id);
CREATE INDEX IF NOT EXISTS idx_orders_driver_id 
    ON de_orders(driver_id);
CREATE INDEX IF NOT EXISTS idx_orders_status 
    ON de_orders(status);

-- Add foreign key constraints for order assignments
ALTER TABLE de_order_assignments
    DROP CONSTRAINT IF EXISTS de_order_assignments_order_id_fkey,
    DROP CONSTRAINT IF EXISTS de_order_assignments_driver_id_fkey;

ALTER TABLE de_order_assignments
    ADD CONSTRAINT de_order_assignments_order_id_fkey
    FOREIGN KEY (order_id)
    REFERENCES de_orders(id);

ALTER TABLE de_order_assignments
    ADD CONSTRAINT de_order_assignments_driver_id_fkey
    FOREIGN KEY (driver_id)
    REFERENCES de_users(id);

-- Add indexes for order assignments
CREATE INDEX IF NOT EXISTS idx_order_assignments_order_id 
    ON de_order_assignments(order_id);
CREATE INDEX IF NOT EXISTS idx_order_assignments_driver_id 
    ON de_order_assignments(driver_id); 