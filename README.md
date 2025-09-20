# REMPAR
Plateforme de simulation de crise inspirée de l’exercice massifié REMPAR25 de l’ANSSI

# Simulation de crise – Exercice inspiré de REMPAR25

## 📌 Contexte

Ce projet est né de l’exercice **REMPAR25**, un exercice de cybersécurité massifié organisé par l’**ANSSI** en 2025 en France.  
L’objectif est de mettre en situation des équipes afin de tester leur réactivité et leur coordination en cas de cyberattaque ou d’incident majeur.  

La plateforme permet de **simuler des canaux de communication réalistes** (réseaux sociaux, stimulus par messagerie interne) alimentés par un scénario défini dans un fichier Excel.  
Elle peut être utilisée lors de formations, de jeux de rôle ou d’exercices de gestion de crise.

---

## 🎯 Objectifs du projet

- Reproduire un environnement immersif simulant :
  - Un **réseau social** type Twitter.
  - Une **messagerie interne** type webmail, avec rôles (RH, Communication, Décision, etc.).
- Fournir aux participants un environnement simple d’accès, utilisable via un navigateur web.
- Permettre aux formateurs / encadrants de suivre la progression de l’exercice :
  - Une **console administrateur** pour charger et suivre le scénario.
  - Une **vue observateur** permettant d’analyser en temps réel l’évolution de l’exercice.

---

## ⚙️ Fonctionnalités principales

### 🔑 Authentification
- Accès **administrateur** protégé par mot de passe.
- Accès **observateur** protégé par un mot de passe distinct.
- Gestion des rôles via la messagerie (Communication, Décision, Informatique, RH, Juridique/Finance, etc.).

### 📊 Administration
- Téléversement du fichier Excel de scénario (`scenario.xlsx`).
- Affichage des événements passés et des prochains messages/tweets planifiés.
- Suivi du nombre total de tweets et messages.

### 🐦 Réseaux sociaux
- Fil d’actualité imitant **Twitter**.
- Affichage des tweets programmés au fil du temps.
- Engagement dynamique (likes, retweets) qui évoluent automatiquement.
- Détection et affichage des **hashtags** tendances.
- Possibilité de filtrer la timeline par hashtag.

### ✉️ Messagerie interne
- Vue **webmail** avec sélection du profil utilisateur.
- Les messages s’affichent au fil de l’eau, en fonction du rôle choisi.
- Ajout d’un **mode “tous”** pour les messages destinés à l’ensemble des rôles.
- Chaque utilisateur peut marquer un message comme **“Traité”** (stocké en local sur son navigateur, sans impact sur les autres).

### 👁️ Observateur
- Accès réservé par mot de passe.
- Timeline affichant uniquement les **messages** (pas les tweets).
- Pour chaque message :
  - ID du stimulus en surbrillance (badge jaune).
  - Horaire de diffusion.
  - **Réaction attendue** (🔎) et **Commentaire** (📝) associés.
- Vue permettant de suivre en parallèle le déroulement et d’évaluer les réactions.

---

## 📂 Structure du scénario (Excel)

Le fichier Excel doit contenir au minimum les colonnes suivantes :

- `id` : identifiant unique du stimulus (pour les messages).
- `horaire` : heure de diffusion (format `HH:MM`).
- `type` : `tweet` ou `message`.
- `emetteur` : auteur du message/tweet.
- `destinataire` : rôle concerné (ou `tous` pour diffusion générale).
- `stimuli` : contenu du message ou du tweet.
- `reaction attendue` *(optionnel)* : ce qui est attendu de l’équipe.
- `commentaire` *(optionnel)* : note pour l’observateur.
- `livrable` *(optionnel)* : sortie attendue (communiqué, rapport, etc.).

---

## 📖 Documentation

Une documentation complète en français expliquant le fonctionnement et la préparation des fichiers Excel est disponible ici :  
➡️ [Documentation/Documentation-fr.md](Documentation/Documentation-fr.md)

---

## 🚀 Installation

### 1. Prérequis
- Python **3.9+**
- Pip et virtualenv

### 2. Installation locale
```bash
git clone https://github.com/jmousqueton/REMPAR.git
cd REMPAR
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Créer un fichier `.env` avec les variables nécessaires :
```env
ADMIN_PASSWORD=MonMotDePasseAdmin
OBSERVER_PASSWORD=MonMotDePasseObservateur
APP_ID=SIM-REMPAR25
FLASK_SECRET=ma-cle-ultra-secrete
```

### 4. Lancer l’application
```bash
python app.py
```

L’application est alors disponible sur [http://localhost:5000](http://localhost:5000).

---

## 👥 Public cible

- **Organisateurs d’exercices de crise** (RSSI, DSI, formateurs).
- **Équipes de communication, juridique, RH, Finance, technique** lors d’un entraînement.
- **Observateurs** chargés d’évaluer la réaction et la coordination.

---

## Démo en ligne

Une instance de démonstration est disponible à l’adresse suivante :  
👉 [https://rempar-demo.mousqueton.io](https://rempar-demo.mousqueton.io)

En mode démo :

- L’accès à l’**Observateur** ne nécessite pas de mot de passe.
- L'accès à l'**administrateur** n'est pas accessible 
- Les autres fonctionnalités (Messagerie, Réseaux sociaux) restent accessibles pour tester le scénario.
- Ce mode est uniquement prévu pour découvrir l’outil.

---

## 🚀 ToDo

- [ ] Ajout d’un **mode clair/sombre** (préférence sauvegardée dans le navigateur)
- [ ] Support **multilingue** (chargement des textes depuis un fichier de traduction)

---

## 📜 Licence

Projet distribué sous licence GNU.  
⚠️  Ce projet est destiné à la **formation et simulation uniquement**.

---

## 🙏 Remerciements

- **ANSSI** pour l’organisation de **REMPAR25**, qui a inspiré cette plateforme.  
- Tous les contributeurs qui enrichissent les exercices de cybersécurité massifiés.
