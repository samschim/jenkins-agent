#!/bin/bash

# GitHub Benutzername (ANPASSEN!)
GITHUB_USER="DEIN_GITHUB_USERNAME"

# Speicherort für Repositories
CLONE_DIR="/root/Repositories"

# Datei zur Speicherung bekannter Repos
KNOWN_REPOS_FILE="/root/known_repos.txt"

# Skript-Pfad für Cron-Job
CHECK_SCRIPT="/root/check_new_repos.sh"

# Installiere jq, falls nicht vorhanden
if ! command -v jq &> /dev/null; then
    echo "🔧 jq wird installiert..."
    apt update && apt install -y jq
fi

# Verzeichnis für Repositories erstellen, falls nicht vorhanden
mkdir -p "$CLONE_DIR"

# Datei mit bekannten Repos erstellen, falls nicht vorhanden
touch "$KNOWN_REPOS_FILE"

# Erstelle das Skript zum Prüfen neuer Repos
cat <<EOF > "$CHECK_SCRIPT"
#!/bin/bash

API_URL="https://api.github.com/users/$GITHUB_USER/repos?per_page=100"

# Neue Repo-Liste abrufen
NEW_REPOS=\$(curl -s "\$API_URL" | jq -r '.[].ssh_url')

for REPO in \$NEW_REPOS; do
    if ! grep -q "\$REPO" "$KNOWN_REPOS_FILE"; then
        echo "Neues Repository gefunden: \$REPO"
        git clone "\$REPO" "$CLONE_DIR/\$(basename "\$REPO" .git)"
        echo "\$REPO" >> "$KNOWN_REPOS_FILE"
    fi
done
EOF

# Skript ausführbar machen
chmod +x "$CHECK_SCRIPT"

# Cron-Job einrichten
CRON_JOB="*/10 * * * * /root/check_new_repos.sh >> /root/check_new_repos.log 2>&1"
(crontab -l 2>/dev/null | grep -v "$CHECK_SCRIPT"; echo "$CRON_JOB") | crontab -

# Sofort einen ersten Check ausführen
echo "🚀 Erster Testlauf..."
bash "$CHECK_SCRIPT"

echo "✅ Einrichtung abgeschlossen! Der Cron-Job läuft nun alle 10 Minuten."
