-- Create the database
CREATE DATABASE IF NOT EXISTS QueryHistory;

-- Use the database
USE QueryHistory;

-- Create Table1: Query
CREATE TABLE IF NOT EXISTS Query (
    query_id INT AUTO_INCREMENT PRIMARY KEY,
    case_type VARCHAR(255),
    case_no VARCHAR(255),
    year VARCHAR(255)
);

-- Create Table2: Responses
CREATE TABLE IF NOT EXISTS Responses (
    response_id INT AUTO_INCREMENT PRIMARY KEY,
    query_id INT,
    case_title VARCHAR(500),
    status VARCHAR(255),
    petitioner VARCHAR(500),
    respondent VARCHAR(500),
    next_date DATE,
    last_date DATE,
    court_no VARCHAR(100),
    order_link TEXT,
    FOREIGN KEY (query_id) REFERENCES Query(query_id) ON DELETE CASCADE
);
