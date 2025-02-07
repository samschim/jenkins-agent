#!/bin/bash

# ==============================
# GitHub SSH Setup Script
# Erstellt einen SSH-Schlüssel und fügt ihn zu GitHub hinzu
# ==============================

set -e  # Stoppt das Skript bei kritischen Fehlern

# === 🔧 KONFIGURATION ===
GH_USERNAME="samschim"  # Dein GitHub-Benutzername
GH_TOKEN=""             # Dein GitHub-Personal Access Token (PAT mit "admin:public_key"-Rechten)

SSH_KEY_PATH="$HOME/.ssh/github_ed25519"  # Standardpfad für den neuen Schlüssel

# === 🛠 VORAUSSETZUNGEN PRÜFEN ===
if [[ -z "$GH_USERNAME" || -z "$GH_TOKEN" ]]; then
    echo "❌ Fehler: Bitte GH_USERNAME und GH_TOKEN in das Skript eintragen!"
    exit 1
fi

if ! command -v gh &>/dev/null; then
    echo "❌ Fehler: GitHub CLI (gh) ist nicht installiert!"
    echo "🔧 Installiere es mit: https://cli.github.com/manual/installation"
    exit 1
fi

# Prüfen, ob bereits ein SSH-Schlüssel existiert
if [[ -f "$SSH_KEY_PATH" ]]; then
    echo "⚠️  SSH-Schlüssel '$SSH_KEY_PATH' existiert bereits."
    read -p "❓ Willst du ihn überschreiben? (y/N): " CONFIRM
    if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
        echo "✅ Bestehender Schlüssel wird verwendet."
    else
        echo "🔄 Erstelle neuen SSH-Schlüssel..."
        rm -f "$SSH_KEY_PATH" "$SSH_KEY_PATH.pub"
        ssh-keygen -t ed25519 -C "$GH_USERNAME" -f "$SSH_KEY_PATH" -N ""
    fi
else
    echo "🔑 Erstelle neuen SSH-Schlüssel..."
    ssh-keygen -t ed25519 -C "$GH_USERNAME" -f "$SSH_KEY_PATH" -N ""
fi

# SSH-Agent starten & Schlüssel hinzufügen
echo "🔄 Starte SSH-Agent und füge Schlüssel hinzu..."
eval "$(ssh-agent -s)"
ssh-add "$SSH_KEY_PATH"

# Öffentlichen Schlüssel auslesen
PUBLIC_KEY=$(cat "$SSH_KEY_PATH.pub")

# Prüfen, ob GitHub CLI bereits authentifiziert ist
if ! gh auth status &>/dev/null; then
    echo "🔑 GitHub CLI ist nicht eingeloggt, Anmeldung wird durchgeführt..."
    echo "$GH_TOKEN" | gh auth login --with-token
else
    echo "✅ GitHub CLI ist bereits eingeloggt."
fi

# SSH-Schlüssel zu GitHub hinzufügen
echo "🚀 Füge SSH-Schlüssel zu GitHub hinzu..."
if gh ssh-key add "$SSH_KEY_PATH.pub" --title "Automatisch generierter Schlüssel"; then
    echo "✅ SSH-Schlüssel wurde erfolgreich zu GitHub hinzugefügt!"
else
    echo "❌ Fehler: SSH-Schlüssel konnte nicht hinzugefügt werden."
    exit 1
fi

echo "🎉 Dein GitHub SSH-Setup ist abgeschlossen! Du kannst jetzt SSH für GitHub nutzen."
echo "👉 Teste die Verbindung mit: ssh -T git@github.com"
