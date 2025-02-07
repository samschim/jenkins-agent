#!/bin/bash

# ==============================
# Git Auto-Update Cron Job Setup (Root Version)
# ==============================

set -e  # Stoppt das Skript bei Fehlern

CRON_FILE="/etc/cron.d/git_repo_update"
UPDATE_SCRIPT="/root/git_update_repos.sh"
REPO_DIR="/root/Repositories"

echo "📁 Stelle sicher, dass das Verzeichnis existiert: $REPO_DIR"
mkdir -p "$REPO_DIR"

# === 📜 ERSTELLEN DES UPDATE-SKRIPTS ===
echo "🔄 Erstelle das Git-Update-Skript..."
cat << 'EOF' > "$UPDATE_SCRIPT"
#!/bin/bash

set -e  # Stoppt das Skript bei Fehlern

REPO_DIR="/root/Repositories"
LOG_FILE="/var/log/git_update.log"

echo "🚀 $(date '+%Y-%m-%d %H:%M:%S') - Starte Git-Update..." | tee -a "$LOG_FILE"

for repo in "$REPO_DIR"/*; do
    if [[ -d "$repo/.git" ]]; then
        echo "🔄 Update Repository: $repo" | tee -a "$LOG_FILE"
        cd "$repo"
        git fetch --all
        BRANCH=$(git remote show origin | awk '/HEAD branch/ {print $NF}')
        git reset --hard "origin/$BRANCH"
        echo "✅ Repository $repo aktualisiert." | tee -a "$LOG_FILE"
    else
        echo "⚠️  $repo ist kein gültiges Git-Repository, wird übersprungen." | tee -a "$LOG_FILE"
    fi
done

echo "🎉 $(date '+%Y-%m-%d %H:%M:%S') - Alle Repositories wurden aktualisiert!" | tee -a "$LOG_FILE"
EOF

# Mach das Skript ausführbar
chmod +x "$UPDATE_SCRIPT"

# === 🕐 ERSTELLEN DES CRON-JOBS ÜBER `/etc/crontab` ===
echo "🛠️  Erstelle den Cron-Job für automatisches Git-Update..."

# Falls bereits ein Cron-Job existiert, ersetze ihn
if grep -q "$UPDATE_SCRIPT" "$CRON_FILE" 2>/dev/null; then
    echo "✅ Cron-Job existiert bereits in $CRON_FILE."
else
    echo "*/5 * * * * root $UPDATE_SCRIPT" > "$CRON_FILE"
    chmod 644 "$CRON_FILE"
    echo "✅ Cron-Job erfolgreich eingerichtet in $CRON_FILE!"
fi

echo "🎉 Automatische Git-Updates alle 5 Minuten eingerichtet!"
