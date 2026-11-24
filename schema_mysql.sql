-- MySQL 8.0.16+ Schema for Student Academic Portal & At-Risk Alert System
CREATE DATABASE IF NOT EXISTS student_portal;
USE student_portal;

CREATE TABLE IF NOT EXISTS students (
    rno INT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    eng INT NOT NULL CHECK (eng >= 0 AND eng <= 100),
    math INT NOT NULL CHECK (math >= 0 AND math <= 100),
    sci INT NOT NULL CHECK (sci >= 0 AND sci <= 100),
    com INT NOT NULL CHECK (com >= 0 AND com <= 100),
    gk INT NOT NULL CHECK (gk >= 0 AND gk <= 100),
    total INT NOT NULL CHECK (total >= 0 AND total <= 500),
    avg DECIMAL(5,2) NOT NULL CHECK (avg >= 0.00 AND avg <= 100.00)
);
