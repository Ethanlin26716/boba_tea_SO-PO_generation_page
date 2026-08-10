CREATE DATABASE infinitea;


CREATE TABLE reorder_results (

    id SERIAL PRIMARY KEY,

    restaurant_code TEXT,

    machine_code TEXT,

    ingredient_code TEXT,

    adjusted_usage DOUBLE PRECISION,

    current_inventory DOUBLE PRECISION,

    target_inventory DOUBLE PRECISION,

    purchased_amount DOUBLE PRECISION,

    inventory_end DOUBLE PRECISION,

    recommended_quantity INTEGER,

    recommended_price DOUBLE PRECISION,

    generated_at TIMESTAMP

);