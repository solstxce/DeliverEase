-- First, drop the existing check constraint
ALTER TABLE de_orders 
    DROP CONSTRAINT IF EXISTS de_orders_status_check;

-- Add the updated check constraint with 'assigned' status
ALTER TABLE de_orders 
    ADD CONSTRAINT de_orders_status_check 
    CHECK (status IN ('pending', 'assigned', 'accepted', 'in_transit', 'delivered', 'completed', 'cancelled'));

-- Update the order assignments table status constraint if needed
ALTER TABLE de_order_assignments 
    DROP CONSTRAINT IF EXISTS de_order_assignments_status_check;

ALTER TABLE de_order_assignments 
    ADD CONSTRAINT de_order_assignments_status_check 
    CHECK (status IN ('pending', 'accepted', 'rejected')); 