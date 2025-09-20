# 📄 Documentation – Compléter le fichier Excel du scénario

Ce fichier Excel permet de définir les **stimuli** qui seront déclenchés automatiquement dans la simulation (tweets, messages ou décompte).

Chaque ligne correspond à un événement.

---

## 🗂️ Colonnes obligatoires

### `id`
- **Uniquement pour les messages**.
- Sert à identifier et ordonner les messages.
- Format recommandé : **numérotation simple et croissante** (`001`, `002`, `003`, …).  
- Exemple : `001` pour le premier message, `002` pour le deuxième, etc.  
- **Attention :** pour les tweets ou les décomptes, laissez cette cellule vide.

---

### `Horaire`
- Heure de déclenchement de l’événement au format **HH:MM**.
- La date du jour est automatiquement utilisée.
- Exemple : `09:15` déclenchera l’événement à 9h15 (heure de Paris).

---

### `Type`
- Type de stimulus attendu :
  - `tweet` → publication sur le flux réseaux sociaux.
  - `message` → arrivée dans la messagerie.
  - `decompte` → affichage d’un compte à rebours (minutes définies dans `stimuli`).

---

### `Emetteur`
- **Obligatoire** pour les `tweet` et les `message`.
- Nom de la personne ou entité qui envoie.
- Exemple : `Direction`, `RSSI`, `Journal Le Monde`.

---

### `Destinataire`
- **Uniquement pour les messages**.
- Correspond au rôle cible du message :
  - `Communication`
  - `Décision`
  - `Informatique`
  - `Juridique / Finance`
  - `Ressources Humaines`
  - `Métier`
  - ou bien `Tous` pour un message général.

---

### `Stimuli`
- Contenu de l’événement.
- Pour un `tweet` → texte du tweet (hashtags autorisés).  
  - **Astuce : vous pouvez insérer une image** en utilisant la syntaxe :  
    ```
    [img nom_du_fichier.png]
    ```
    Les images doivent être présentes dans le dossier **`static/images/`** du projet.  
    👉 Elles peuvent être **téléversées directement via l’interface d’administration** (section *Upload image*).  
    Exemple : `Nouvelle fuite révélée ! [img fuite.png]`
- Pour un `message` → texte du mail reçu.  
- Pour un `decompte` → durée du compte à rebours en minutes (exemple : `15`).

---

## 📝 Colonnes optionnelles

### `Réaction attendue`
- Indique la réponse souhaitée des participants.  
- Exemple : *"Prévenir le service communication"*.

### `Commentaire`
- Informations complémentaires destinées aux animateurs de l’exercice.

### `Livrable`
- Indique un document attendu (exemple : *"Rédiger un communiqué de presse"*).

---

## ✅ Exemple de tableau

| id   | Horaire | Type     | Emetteur      | Destinataire   | Stimuli                                   | Réaction attendue                  | Commentaire              | Livrable               |
|------|---------|----------|---------------|----------------|-------------------------------------------|------------------------------------|--------------------------|------------------------|
|      | 09:00   | tweet    | Journal Info  |                | #Cyberattaque en cours ! [img fuite.png]   | Analyser l’impact médiatique       | Premier tweet public     |                        |
| 001  | 09:05   | message  | RSSI          | Informatique   | Incident détecté sur serveur X             | Isoler le serveur                   | Données techniques       | Rapport d’analyse      |
|      | 09:10   | decompte |               |                | 15                                        | Attendre fin du décompte           | Pause simulation 15 min  |                        |
| 002  | 09:20   | message  | Direction     | Communication  | Préparer un communiqué officiel           | Élaborer une communication interne | Vérifier cohérence texte | Communiqué interne     |

---

👉 Avec cette structure, la simulation sait **quoi déclencher, quand, et pour qui**.
