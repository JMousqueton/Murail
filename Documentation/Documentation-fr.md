# 📄 Documentation

## 📂 Structure des fichiers Excel

La plateforme utilise maintenant **deux fichiers Excel distincts** :

### 1️⃣ Chronogramme (`chronogramme.xlsx`)
Ce fichier contient les **messages et événements de décompte**.

### 2️⃣ PMS (`pms.xlsx`) — *Optionnel*
Ce fichier contient les **tweets** (réseaux sociaux).
- ⚠️ Nécessite `ENABLE_PMS=true` dans le fichier `.env`
- Si `ENABLE_PMS=false`, le module social media est désactivé.

---

## ⚙️ Compléter le fichier Chronogramme (`chronogramme.xlsx`)

Ce fichier Excel permet de définir les **messages** et **décomptes** qui seront déclenchés automatiquement dans la simulation.

Chaque ligne correspond à un événement.

---

### 🗂️ Colonnes obligatoires

#### `id`
- **Uniquement pour les messages**.
- Sert à identifier et ordonner les messages.
- Format recommandé : **numérotation simple et croissante** (`001`, `002`, `003`, …).  
- Exemple : `001` pour le premier message, `002` pour le deuxième, etc.  
- **Attention :** pour les décomptes, laissez cette cellule vide.

---

#### `Horaire`
- Heure de déclenchement de l'événement au format **HH:MM** ou **HH:MM:SS**.
- La date du jour est automatiquement utilisée.
- Exemple : `09:15` déclenchera l'événement à 9h15 (heure de Paris).

---

#### `Type`
- Type de stimulus attendu :
  - `message` → arrivée dans la messagerie interne.
  - `decompte` → affichage d'un compte à rebours (minutes définies dans `stimuli`).

**Note :** Les tweets sont maintenant gérés dans le fichier **`pms.xlsx`** séparé.

---

#### `Emetteur`
- **Obligatoire** pour les messages.
- Nom de la personne ou entité qui envoie.
- Exemple : `Direction`, `RSSI`, `Communication`.

---

#### `Destinataire`
- **Uniquement pour les messages**.
- Correspond au rôle(s) cible(s) du message.
- **Les rôles sont dynamiquement extraits** à partir de vos destinataires → pas besoin de liste prédéfinie !
- Exemples courants :
  - `Communication`
  - `Décision`
  - `Informatique`
  - `Juridique / Finance`
  - `Ressources Humaines`
  - `Métier`
  - `Tous` → message pour **tous les rôles**.

**💡 Support multi-destinataires** : pour envoyer un message à plusieurs rôles, listez-les sur plusieurs lignes avec le même `id` :

| id  | Horaire | Type    | Emetteur | Destinataire | Stimuli           |
|-----|---------|---------|----------|--------------|-------------------|
| 003 | 10:00   | message | RSSI     | Informatique | Serveur down      |
|     |         |         |          | Décision     |                   |

⚠️ **Alternative** : vous pouvez aussi utiliser un saut de ligne dans la même cellule Excel pour lister plusieurs destinataires.

---

#### `Stimuli`
- Contenu de l'événement.
- Pour un `message` → texte du mail reçu.  
- Pour un `decompte` → durée du compte à rebours en minutes (exemple : `15`).

---

### 📝 Colonnes optionnelles

Ces colonnes sont uniquement à destination du rôle d'animateur/facilitateur.

#### `Réaction attendue`
- Indique la réponse souhaitée des participants.  
- Exemple : *"Prévenir le service communication"*.

#### `Commentaire`
- Informations complémentaires destinées aux animateurs de l'exercice.

#### `Livrable`
- Indique un document attendu (exemple : *"Rédiger un communiqué de presse"*).

---

### ✅ Exemple de tableau (Chronogramme)

| id   | Horaire | Type     | Emetteur      | Destinataire   | Stimuli                       | Réaction attendue              | Commentaire         | Livrable          |
|------|---------|----------|---------------|----------------|-------------------------------|--------------------------------|---------------------|-------------------|
| 001  | 09:05   | message  | RSSI          | Informatique   | Incident détecté sur serveur  | Isoler le serveur              | Données techniques  | Rapport d'analyse |
|      | 09:10   | decompte |               |                | 15                            | Attendre fin du décompte       | Pause 15 min        |                   |
| 002  | 09:20   | message  | Direction     | Communication  | Préparer un communiqué        | Élaborer communication interne  | Vérifier texte      | Communiqué        |
| 003  | 09:30   | message  | RSSI          | Tous           | Situation générale à 9h30     | Briefing en direct             |                     |                   |

---

## ⚙️ Compléter le fichier PMS (`pms.xlsx`)

Ce fichier Excel contient les **tweets** qui s'afficheront sur le fil réseaux sociaux.

**⚠️ Prérequis :** `ENABLE_PMS=true` dans le fichier `.env`

### 🗂️ Colonnes obligatoires

#### `Horaire`
- Heure de publication du tweet au format **HH:MM** ou **HH:MM:SS**.
- Exemple : `09:15`

#### `Emetteur`
- **Obligatoire**.
- Compte Twitter simulé (auteur du tweet).
- Exemple : `Journal Info`, `ANSSI Official`, `@CyberDefense`.

Si l'`Emetteur` est `aléatoire`, un pseudo sera choisi aléatoirement depuis le fichier `tweet.txt` du répertoire `static/data`.

Si un fichier `Emetteur.png` ou `Emetteur.jpg` existe dans `static/images/tweet/`, il sera utilisé comme avatar.

#### `Stimuli`
- Contenu du tweet (hashtags autorisés).
- **Astuce : vous pouvez insérer une image** en utilisant la syntaxe :
  ```
  [img nom_du_fichier.png]
  ```
  Les images doivent être présentes dans le dossier **`static/images/`**.
  👉 Elles peuvent être **téléversées directement via l'interface d'administration** (section *Upload image*).
  
  Exemple : `Nouvelle fuite révélée ! [img fuite.png]`

### ✅ Exemple de tableau (PMS)

| Horaire | Emetteur      | Stimuli                                   |
|---------|---------------|-------------------------------------------|
| 09:00   | Journal Info  | #Cyberattaque en cours ! [img fuite.png] |
| 09:15   | @CyberDefense | Nos experts analysent la situation        |
| 09:30   | ANSSI         | Alertes de sécurité niveau 3              |

---

👉 Avec cette structure, la simulation sait **quoi déclencher, quand, et pour qui**.


## 🖥️ Interface utilisateur

L'application propose plusieurs interfaces web permettant aux participants et aux animateurs de suivre le déroulement de l'exercice.

---

### 📌 Page d'accueil (`/`)

- **Vue générale** de l'exercice.
- Affiche :
  - Les accès vers les différentes interfaces (Réseaux sociaux, Messagerie, Observateur, Administration).
  - Le statut du scénario (chargé ou vide).
  - Les **5 derniers événements** déclenchés (messages uniquement).
- Sert de point d'entrée pour les participants.

![Accueil](img/accueil.png)

---

### 🐦 Réseaux sociaux (`/socialmedia`)

- Simule un **flux type Twitter**.
- Fonctionnalités :
  - Affichage des **tweets** programmés dans le scénario.
  - Support des **hashtags** → les tendances s'actualisent en temps réel dans la colonne de droite.
  - Possibilité d'inclure des **images** dans les tweets via la syntaxe `[img nom.png]`.
  - Affichage dynamique du **nombre de retweets et de likes**, qui évoluent automatiquement.
  - Filtrage par hashtag actif → cliquer sur un sujet de tendance limite l'affichage aux tweets correspondants.
- Une horloge (heure de Paris) est visible en haut à droite.

![Réseaux sociaux](img/mediassociaux.png)

---

### ✉️ Messagerie (`/messagerie`)

- Simule une **messagerie interne** (type Outlook / Webmail).
- Fonctionnalités :
  - Chaque participant choisit son **rôle** (Communication, Décision, Informatique, RH, etc.).
  - La boîte de réception affiche les **messages adressés à ce rôle**.
  - Les messages peuvent être **ouverts et consultés**.
  - Chaque message peut être marqué comme **traité** ✅ (stockage local, persistant par rôle).
  - L'historique des 100 derniers messages est disponible au chargement.
  - Flux en temps réel grâce au **SSE** (Server-Sent Events).

![Messagerie](img/messagerie.png)

---

### 🔎 Animateur (`/animateur`)

- Réservé aux **animateurs / contrôleurs**.
- Accès via mot de passe (ou prérempli en mode démo).
- Fonctionnalités :
  - Vue synthétique des **messages diffusés**.
  - Les **5 derniers messages**.
  - Les **2 prochains messages** programmés.
  - Affichage des **réactions attendues** et **commentaires** définis dans le fichier Excel.

![Animateur](img/animateur.png)

---

### 👁️ Observateur (`/observateur`)

- Réservé aux **observateurs / évaluateurs**.  
- Accès via mot de passe.  
- Fonctionnalités :  
  - Vue centrée sur les **stimuli (messages)** de l'exercice.  
  - Le **prochain message** est affiché en haut, grisé et inactif jusqu'à son horaire.  
  - Les **messages passés** apparaissent en ordre inverse chronologique (le plus récent en premier).  
  - Pour chaque stimulus, l'observateur peut :  
    - Donner une **appréciation rapide** (👍 / 👎).  
    - Ajouter un **commentaire libre**.  
  - Les notes sont **sauvegardées automatiquement** en local (navigateur).  
  - Possibilité d'**exporter** les observations en **JSON** ou **CSV** pour analyse et debriefing.  

![Observateur](img/observateur.png)

---

### ⚙️ Administration (`/admin`)

- Réservée aux **administrateurs** (mot de passe requis).
- Fonctionnalités :
  - **Charger le Chronogramme** (fichier Excel avec messages et décomptes).
  - **Charger le PMS** (fichier Excel avec tweets) — optionnel si `ENABLE_PMS=true`.
  - Voir les événements passés et futurs.
  - **Téléverser des images** (qui pourront être utilisées dans les tweets via `[img nom.png]`).
  - Indicateurs de statut :
    - ✅ Chronogramme chargé / ❌ Vide
    - ✅ PMS chargé / ❌ Vide / ⊘ Désactivé

  ![Admin](img/admin.png)

---

### ⏳ Décompte

- Lorsque le scénario contient un stimulus de type **`decompte`** :
  - Les interfaces du joueur (Messagerie et Médias Sociaux) basculent automatiquement vers une **page de compte à rebours plein écran**.
  - La page d'accueil affiche aussi le décompte.
  - Le minuteur s'affiche avec un effet lumineux rouge.
  - À la fin du décompte, les interfaces Messagerie et Réseaux Sociaux reviennent à la normale automatiquement.

![Decompte](img/decompte.png)

---

## ⚙️ Fichier `.env`

Le fichier `.env` permet de configurer l'application sans modifier le code.  
Il contient les paramètres sensibles (mots de passe, identifiants, secrets) et les chemins de fichiers.

**👉 Voir [env.example](../env.example) pour une description détaillée de toutes les variables.**

### Détails des principales variables

#### Authentification
- **`ADMIN_PASSWORD`** : mot de passe pour accéder à l'interface **Administration**.  
- **`ANIMATOR_PASSWORD`** : mot de passe pour accéder à l'interface **Animateur**.
- **`OBSERVER_PASSWORD`** : mot de passe pour accéder à l'interface **Observateur**.

#### Configuration globale
- **`APP_ID`** : identifiant unique de l'instance de simulation (utile pour différencier plusieurs environnements).  
- **`FLASK_SECRET`** : clé secrète utilisée par Flask pour gérer les sessions utilisateurs (⚠️ doit être **unique et complexe**).
  - Générer une clé : `python3 -c "import secrets; print(secrets.token_hex(32))"`
- **`TZ`** : fuseau horaire de l'application (par défaut : `Europe/Paris`).
- **`LANG`** : langue par défaut (par défaut : `fr` pour français, ou `en` pour anglais).
- **`PORT`** : port d'écoute de l'application (par défaut : `5000`).

#### Fichiers scénarios
- **`CHRONOGRAMME_FILE`** : chemin vers le fichier Excel des **messages et décomptes** (par défaut : `Sample/chronogramme.xlsx`).
- **`ENABLE_PMS`** : active/désactive le module PMS (tweets).
  - `true` → module actif, `false` → module désactivé.
- **`PMS_FILE`** : chemin vers le fichier Excel des **tweets** (par défaut : `Sample/pms.xlsx`, utilisé si `ENABLE_PMS=true`).

#### Mode et débogage
- **`DEBUG`** : active le mode débogage Flask (⚠️ ne pas activer en production).
- **`DEMO`** : active le **mode démo**.
  - `true` → les mots de passe Animateur et Observateur sont pré-remplis automatiquement.
  - Admin est inaccessible.
- **`TRACKING`** : permet d'ajouter un script de suivi analytique (exemple : **Matomo**, Google Analytics…).
   - Le contenu est injecté tel quel dans le bas de chaque page.
   - Exemple typique : un script Matomo hébergé sur un serveur interne.

👉 **Conseil sécurité** : ne jamais partager publiquement le contenu réel du fichier `.env` (surtout les mots de passe et `FLASK_SECRET`).

---

### 🧪 Mode Démo

- Une instance de démonstration est disponible :  
  👉 [https://murail-demo.mousqueton.io](https://murail-demo.mousqueton.io)  
- Dans ce mode (`DEMO=true`) :
  - Le mot de passe **Animateur** est pré-rempli automatiquement.
  - Le mot de passe **Observateur** est pré-rempli automatiquement.
  - L'accès **Admin** est **désactivé**.
  - Les autres fonctionnalités (Messagerie, Réseaux sociaux) restent accessibles.
  - Permet de tester facilement l'interface sans configuration locale.
