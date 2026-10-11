**GlobalShop — Base de données distribuée**

**Projet de Master 2 — Gestion des Données et Ingénierie Logicielle (GDIL)**  
**Université Gaston Berger de Saint-Louis — Sénégal**

## 1. Présentation du projet

GlobalShop est un prototype de commerce électronique utilisant une architecture de base de données distribuée. Le projet permet d'étudier la répartition des données, le routage des requêtes, la réplication PostgreSQL, la gestion des achats concurrents et la résilience en cas de panne.

L'architecture repose sur FastAPI, quatre nœuds PostgreSQL et Docker Compose.

## 2. Objectifs

- Distribuer les produits sur quatre nœuds PostgreSQL.
- Router les requêtes vers le nœud propriétaire du produit.
- Empêcher la vente d'une quantité supérieure au stock disponible.
- Répliquer les données entre les nœuds.
- Tester le comportement du système pendant une panne et après le redémarrage d'un nœud.

## 3. Architecture du système


                  CLIENT
                    |
                    v
              API FASTAPI
               Port 8000
                    |
                    v
          ROUTAGE PAR IDENTIFIANT
                    |
          +---------+---------+
          |         |         |
          v         v         v
       Node 1    Node 2    Node 3    Node 4
       Afrique   Europe    Amérique  Asie
          |         |         |        |
          +---------+---------+--------+
                    |
                    v
           RÉPLICATION LOGIQUE


Les régions sont des étiquettes logiques : les quatre nœuds fonctionnent dans l'environnement Docker local.

## 4. Sharding des produits

Le sharding répartit les produits entre les quatre nœuds à partir de leur identifiant.

La règle utilisée est :


product_id % 4


La répartition est la suivante :


Reste 1  -> Node 1 -> Afrique
Reste 2  -> Node 2 -> Europe
Reste 3  -> Node 3 -> Amérique
Reste 0  -> Node 4 -> Asie

exemple :
product_id = 13
13 % 4 = 1
       |
       v
     Node 1


Cette méthode est simple, rapide et déterministe. Cependant, changer le nombre de nœuds peut nécessiter une redistribution des données.

## 5. Routage des requêtes

Le routeur FastAPI reçoit les requêtes du client, détermine le nœud propriétaire du produit et transmet la requête à la base correspondante.


Client
   |
   v
API FastAPI
   |
   v
Calcul product_id % 4
   |
   v
Sélection du nœud propriétaire
   |
   v
Requête PostgreSQL
   |
   v
Réponse au client


## 6. Réplication et résilience

Le projet utilise la réplication logique PostgreSQL avec des publications filtrées selon les partitions.

Node 1
   |
   v
Node 2
   |
   v
Node 3
   |
   v
Node 4
   |
   v
Node 1

La réplication est asynchrone. Une copie peut donc temporairement être en retard.

Lorsqu'un nœud est indisponible, le routeur peut essayer un autre nœud pour une lecture. En revanche, le basculement automatique et sécurisé des écritures n'est pas garanti par l'implémentation actuelle.

## 7. Gestion de la concurrence

Lors d'un achat, une mise à jour SQL conditionnelle décrémente le stock uniquement si la quantité demandée est disponible.


UPDATE produit
SET stock = stock - %s
WHERE product_id = %s
  AND stock >= %s
RETURNING product_id, nom, stock;


Cette opération évite la survente dans le scénario testé en laissant PostgreSQL gérer les mises à jour concurrentes d'une même ligne.

## 8. Endpoints de l'API

L'API est accessible sur le port `8000`.

- `GET /` -> vérification simple de l'API.
- `GET /health` -> vérification de l'état du routeur.
- `GET /produits/{product_id}` -> récupération d'un produit avec tentative de repli en lecture.
- `POST /acheter` -> tentative d'achat d'un produit.

Principaux codes de réponse :

- `200` -> achat accepté.
- `404` -> produit introuvable.
- `409` -> stock insuffisant.
- `503` -> service ou base de données indisponible.

## 9. Prérequis

Installer les outils suivants :

- Docker Desktop
- Git
- Un terminal compatible avec Docker

Vérifier les installations :

```bash
docker --version
docker compose version
git --version
```

## 10. Installation et lancement

Cloner le dépôt GitHub :

```bash
git clone https://github.com/bamarieme-ui/Global.git
cd Global
```

Démarrer les services :

```bash
docker compose up -d --build
```

Vérifier les conteneurs :

```bash
docker compose ps
```

Tester l'API :

```bash
curl http://localhost:8000/health
```

Sous PowerShell, si nécessaire :

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Afficher les journaux :

```bash
docker compose logs -f
```

Arrêter les services :

```bash
docker compose down
```

## 11. Structure du dépôt

```text
Global/
   |
   |---- README.md
   |
   |---- docker-compose.yml
   |
   |---- démo.sh
   |
   |---- base de données/
   |        |
   |        |---- fichiers SQL et configuration PostgreSQL
   |
   |---- routeur/
   |        |
   |        |---- code FastAPI
   |        |---- fichiers nécessaires au lancement de l'API
   |
   |---- tests/
            |
            |---- tests de concurrence
            |---- tests de résilience

- base de données : contient les fichiers SQL et les éléments de configuration des quatre nœuds PostgreSQL.
- routeur/ : contient le code de l'API FastAPI et les fichiers nécessaires à son exécution.
- tests/ : regroupe les scripts de test de concurrence et de résilience.
- docker-compose.yml : définit les services et leur configuration pour lancer l'application.
- démo.sh : automatise le démarrage et la vérification de l'application.
- README.md : présente le projet, son architecture et les instructions d'installation et d'utilisation.


Cette représentation décrit les éléments visibles dans le dépôt. Les noms et contenus exacts des fichiers à l'intérieur des dossiers peuvent varier.

## 12. Résultats des tests

### Test de concurrence

Le test a envoyé 100 achats simultanés pour un produit dont le stock initial était de 10.

```text
Stock initial : 10
       |
       v
100 achats simultanés
       |
       +----> 10 achats acceptés (HTTP 200)
       |
       +----> 90 achats refusés (HTTP 409)
       |
       v
Stock final : 0
```

Aucune erreur inattendue n'a été observée. Le résultat montre que le stock initial n'a pas été dépassé dans ce scénario.

### Test de panne pendant les écritures

```text
Stock initial : 10 000
       |
       v
Test pendant une panne
       |
       +----> 2 427 réponses HTTP 200
       |
       +----> 184 réponses HTTP 503
       |
       +----> 45 expirations de délai
       |
       v
Stock observé après récupération : 7 573
```

La diminution du stock correspond aux 2 427 réponses HTTP 200. Les expirations de délai restent ambiguës : une opération peut avoir été appliquée sans que sa réponse soit arrivée au client.

### Repli en lecture et récupération

Pendant l'arrêt de Node 1, une lecture a été servie par Node 2.

```text
Node 1 indisponible
       |
       v
Tentative de lecture
       |
       v
Node 2
       |
       v
Réponse au client
```

Après redémarrage, PostgreSQL a de nouveau accepté les connexions. Lors d'une vérification ultérieure distincte, le stock du produit 13 était de 4 250 sur Node 1 et Node 2.

Ces observations correspondent à des scénarios différents. Elles ne garantissent pas l'absence de perte de données dans toutes les situations.

## 13. Limites et améliorations

Les limites identifiées sont :

- Les quatre nœuds fonctionnent localement : aucune latence intercontinentale réelle n'a été mesurée.
- La réplication asynchrone peut présenter un retard.
- Le basculement sécurisé des écritures n'est pas entièrement automatisé.
- Les expirations de délai peuvent rendre le résultat d'un achat ambigu.
- Des tests supplémentaires sont nécessaires pour évaluer d'autres charges et pannes.

Améliorations envisagées :

```text
Clés d'idempotence
       |
       v
Basculement contrôlé
       |
       v
Mesure du retard de réplication
       |
       v
Journalisation détaillée
       |
       v
Tests supplémentaires
```

## 14. Démonstration

Si le script `démo.sh` est présent à la racine du dépôt et compatible avec Bash, le lancer avec :

```bash
bash démo.sh
```

Le script permet de démarrer les services et de vérifier l'état de l'API. Les tests peuvent être exécutés séparément selon les scripts disponibles dans le dossier `tests/`.

## 15. Conclusion

GlobalShop est un prototype pédagogique qui met en pratique le sharding, le routage FastAPI, la réplication logique PostgreSQL, la concurrence sur le stock et le repli en lecture.

Le test de 100 achats montre que le stock initial de 10 n'a pas été dépassé dans le scénario mesuré. Les essais de panne montrent l'intérêt du repli en lecture, mais aussi les limites de continuité des écritures et l'ambiguïté des expirations de délai.

## 16. Références

- PostgreSQL — https://www.postgresql.org/docs/current/
- FastAPI — https://fastapi.tiangolo.com/
- Docker Compose — https://docs.docker.com/compose/
- Psycopg — https://www.psycopg.org/docs/

---

**Projet académique — GlobalShop**  
Université Gaston Berger de Saint-Louis, Sénégal.

























