CREATE TABLE client (
    customer_id INTEGER PRIMARY KEY,
    nom VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    customer_region VARCHAR(30) NOT NULL
);

CREATE TABLE produit (
    product_id INTEGER PRIMARY KEY,
    nom VARCHAR(150) NOT NULL,
    prix NUMERIC(10,2) NOT NULL,
    stock INTEGER NOT NULL
);

CREATE TABLE commande (
    order_id INTEGER PRIMARY KEY,
    customer_id INTEGER NOT NULL,
    customer_region VARCHAR(30) NOT NULL,
    statut VARCHAR(30) NOT NULL,
    date_commande TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE ligne_commande (
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantite INTEGER NOT NULL,
    prix_unitaire NUMERIC(10,2) NOT NULL,

    PRIMARY KEY (order_id, product_id)
);