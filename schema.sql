CREATE DATABASE sims;

USE sims;

CREATE TABLE
users(
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fullname varchar(100) NOT NULL,
    username varchar(50) NOT NULL UNIQUE, 
    email varchar(100) NOT NULL UNIQUE,
    phone varchar(20) NOT NULL,
    password varchar(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()

)


CREATE TABLE
    categories (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        status ENUM ('active', 'inactive') DEFAULT 'active',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    );


