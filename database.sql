CREATE DATABASE IF NOT EXISTS expense_tracker
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE expense_tracker;

-- Utilisateurs
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    currency VARCHAR(10) DEFAULT 'XOF',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Catégories
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NULL,
    name VARCHAR(80) NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    icon VARCHAR(50) DEFAULT 'category',
    color VARCHAR(20) DEFAULT '#635BFF',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    UNIQUE KEY unique_category (user_id, name, type)
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    type ENUM('income', 'expense') NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    description VARCHAR(255) DEFAULT NULL,
    transaction_date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT,
    INDEX idx_user_date (user_id, transaction_date),
    INDEX idx_user_type (user_id, type)
);

-- Budgets mensuels
CREATE TABLE IF NOT EXISTS budgets (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    category_id INT NOT NULL,
    budget_month DATE NOT NULL,
    amount_limit DECIMAL(12, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE,
    UNIQUE KEY unique_budget (user_id, category_id, budget_month)
);

-- Catégories par défaut
INSERT INTO categories (user_id, name, type, icon, color) VALUES
(NULL, 'Salaire', 'income', 'work', '#22C55E'),
(NULL, 'Freelance', 'income', 'laptop', '#22C55E'),
(NULL, 'Autres revenus', 'income', 'savings', '#22C55E'),
(NULL, 'Alimentation', 'expense', 'restaurant', '#F59E0B'),
(NULL, 'Transport', 'expense', 'directions_bus', '#3B82F6'),
(NULL, 'Logement', 'expense', 'home', '#8B5CF6'),
(NULL, 'Santé', 'expense', 'medical_services', '#EF4444'),
(NULL, 'Loisirs', 'expense', 'sports_esports', '#EC4899'),
(NULL, 'Éducation', 'expense', 'school', '#06B6D4'),
(NULL, 'Autres dépenses', 'expense', 'category', '#64748B');