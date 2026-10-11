#!/usr/bin/env bash
set -Eeuo pipefail

# GlobalShop — script de démonstration
# Compatible avec Bash (Linux, macOS, Git Bash ou WSL).
# Le script démarre les services et vérifie l'API.
# Il ne lance PAS automatiquement les tests destructifs ou de chaos.

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "======================================"
echo "       DEMONSTRATION GLOBALSHOP"
echo "======================================"
echo

if ! command -v docker >/dev/null 2>&1; then
  echo "ERREUR : Docker n'est pas installé ou n'est pas accessible dans PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "ERREUR : Docker Compose (plugin 'docker compose') est requis." >&2
  exit 1
fi

echo "[1/4] Démarrage des conteneurs..."
docker compose up -d --build

echo
echo "[2/4] État des services Docker Compose..."
docker compose ps

echo
echo "[3/4] Vérification de l'API FastAPI..."
if command -v curl >/dev/null 2>&1; then
  if ! curl --fail --silent --show-error "${BASE_URL}/health"; then
    echo
    echo "ERREUR : l'API ne répond pas correctement sur ${BASE_URL}/health." >&2
    echo "Consulte les logs avec : docker compose logs --tail=100 router" >&2
    exit 1
  fi
  echo
else
  echo "curl n'est pas disponible ; vérification HTTP ignorée."
fi

echo
echo "[4/4] Démonstration prête."
echo "Endpoints utiles :"
echo "  Santé API       : ${BASE_URL}/health"
echo "  Lire un produit : ${BASE_URL}/produits/13"
echo
echo "Tests Python (à exécuter séparément depuis le dossier du projet) :"
echo "  Windows PowerShell : .\.venv\Scripts\python.exe .\tests\test_achats.py"
echo "  Bash/Linux/WSL     : python tests/test_achats.py"
echo
echo "Test Chaos Engineering (à exécuter uniquement quand tu es prêt à arrêter Node 1) :"
echo "  Windows PowerShell : .\.venv\Scripts\python.exe .\tests\chaos_ecriture.py"
echo "  Bash/Linux/WSL     : python tests/chaos_ecriture.py"
echo
echo "Attention : les tests modifient le stock. Le test de chaos nécessite"
echo "une action manuelle séparée pour arrêter/redémarrer le nœud selon le protocole."
