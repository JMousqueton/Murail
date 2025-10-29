# Mur@il
Crisis simulation platform inspired by the large-scale **REMPAR25** exercise organized by **ANSSI**

# Crisis Simulation – Exercise inspired by REMPAR25

## 📌 Context

This project was born from the **REMPAR25** cybersecurity exercise, a large-scale simulation organized by **ANSSI** in France in 2025.  
Its purpose is to put teams in realistic conditions to test their responsiveness and coordination in case of a cyberattack or major incident.

The platform allows you to **simulate realistic communication channels** (social media feeds, internal messaging stimuli) driven by a scenario defined in an Excel file.  
It can be used for trainings, role-playing sessions, or crisis management exercises.

---

## 🎯 Project Objectives

- Reproduce an immersive environment simulating:
  - A **social network** similar to Twitter.
  - An **internal messaging system** (webmail-like) with user roles (HR, Communication, Decision, etc.).
- Provide participants with an easy-to-access environment usable directly in a web browser.
- Allow trainers/facilitators to monitor the progress of the exercise:
  - An **admin console** to load and monitor the scenario.
  - An **animator view** to analyze the exercise in real time.

---

## ⚙️ Main Features

### 🔑 Authentication
- **Admin** access protected by password.
- **Animator** access protected by a distinct password.
- Role-based access for messaging (Communication, Decision, IT, HR, Legal/Finance, etc.).

### 📊 Administration
- Upload the scenario Excel file (`scenario.xlsx`).
- View past events and upcoming messages/tweets.
- Monitor the total number of tweets and messages.

### 🐦 Social Media
- Feed simulating **Twitter**.
- Displays tweets scheduled in the scenario.
- Dynamic engagement (likes, retweets) evolves automatically.
- Detection and display of trending **hashtags**.
- Option to filter the timeline by hashtag.

### ✉️ Internal Messaging
- **Webmail** view with user role selection.
- Messages appear over time depending on the selected role.
- Includes a **“All” mode** for messages addressed to all roles.
- Each user can mark messages as **“Processed”** (locally stored in their browser, no global effect).

### 🪄 Animator
- Password-protected access.
- Timeline showing only **messages** (not tweets).
- For each message:
  - Stimulus ID highlighted (yellow badge).
  - Scheduled time of delivery.
  - Associated **Expected Reaction** (🔎) and **Comment** (📝).
- Allows real-time follow-up and evaluation of reactions.

### 👁️ Observer
- Password-protected access.
- Timeline showing only **messages** (not tweets).
- For each message, the observer can rate the crisis team’s reaction with a thumbs up 👍 or down 👎 and add a comment.  
- Entered data is stored locally in the observer’s browser.  
- Export in JSON or CSV format.

---

## 📂 Scenario Structure (Excel)

The Excel file must contain at least the following columns:

- `id`: unique stimulus identifier (for messages).  
- `horaire`: broadcast time (`HH:MM` format).  
- `type`: `tweet` or `message`.  
- `emetteur`: sender of the message/tweet.  
- `destinataire`: target role (or `tous` for general broadcast).  
- `stimuli`: message or tweet content.  
- `reaction attendue` *(optional)*: expected reaction from the team.  
- `commentaire` *(optional)*: note for the facilitator.  
- `livrable` *(optional)*: expected output (press release, report, etc.).  

---

## 📖 Documentation

A complete documentation in French explaining how to configure and prepare the Excel scenario file is available here:  
➡️ [Documentation/Documentation-fr.md](Documentation/Documentation-en.md)

---

## 🚀 Installation

### 1. Requirements
- Python **3.9+**
- Pip and virtualenv

### 2. Local installation
```bash
git clone https://github.com/jmousqueton/murail.git
cd murail
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. Configuration
Create a `.env` file with the required variables:
```env
ADMIN_PASSWORD=MyAdminPassword
ANIMATOR_PASSWORD=MyAnimatorPassword
OBSERVER_PASSWORD=MyObserverPassword
APP_ID=SIM-MURAIL
FLASK_SECRET=my-ultra-secret-key
TZ=Europe/Paris
```

### 4. Launch the application
```bash
python app.py
```

The application will then be available at [http://localhost:5000](http://localhost:5000).

---

## 👥 Target Audience

- **Crisis exercise organizers** (CISO, CIO, trainers).  
- **Communication, Legal, HR, Finance, Technical teams** during training.  
- **Facilitators** evaluating reaction and coordination.

---

## 💻 Online Demo

A demo instance is available at:  
👉 [https://murail-demo.mousqueton.io](https://murail-demo.mousqueton.io)

In demo mode:

- **Animator** access requires no password.  
- **Observer** access requires no password.  
- **Administrator** access is disabled.  
- Other features (Messaging, Social Media) remain accessible for testing scenarios.  
- This mode is intended solely for demonstration purposes.

---

## 🚀 To-Do List

- [ ] Add **light/dark mode** (preference saved in browser).  
- [ ] Allow publishing of user tweets (limited to communication role).  
- [ ] Generate a PDF from **observer** feedback.  

---

## 📜 License

Project distributed under **GNU License**.  
⚠️ This project is intended for **training and simulation purposes only**.

---

## 🙏 Acknowledgments

- **ANSSI** for organizing **REMPAR25**, which inspired this platform.  
- All contributors who enhance large-scale cybersecurity exercises.
