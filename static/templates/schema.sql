CREATE DATABASE sims;

USE sims;

CREATE TABLE
users(
    id int NOT NULL AUTO_INCREMENT PRIMARY KEY,
    fullname varchar(100) NOT NULL,
    username varchar(50) NOT NULL, 
    email varchar(100) NOT NULL,
    phone varchar(20) NOT NULL,
    password varchar(500) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()

)