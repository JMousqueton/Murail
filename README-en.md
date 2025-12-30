➡️ [Lire cette documentation en français](README.md)

# Mur@il
Crisis simulation platform inspired by the **REMPAR25** exercise by **ANSSI**

# Crisis Simulation – Exercise Inspired by REMPAR25

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
- Upload scenario Excel file (`chronogramme.xlsx`).
- Upload social media Excel file (`PMS.xlsx`).
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
- Includes an **"All" mode** for messages addressed to all roles.
- Each user can mark a message as **"Processed"** (stored locally in browser, no impact on other users).

### 🪄 Animator
- Password-protected access.
- Timeline displaying **messages only** (no tweets).
- For each message:
  - Stimulus ID highlighted (yellow badge).
  - Delivery time.
  - **Expected reaction** (🔎) and **Comment** (📝).
- View to monitor the exercise in real time and evaluate team reactions.

### 👁️ Observer
- Password-protected access.
- Timeline displaying **messages only** (no tweets).
- For each message, the observer can note the crisis team's reaction with thumbs up 👍 or down 👎 and add a comment.
- Information is stored locally in the browser.
- Export in JSON or CSV format.

---

## 📂 Scenario File Structure (Excel)

The platform uses **two separate Excel files**:

### 1. **Chronogramme** (messages and events)
The Excel file `chronogramme.xlsx` must contain at least the following columns:

- `id` : unique stimulus identifier (for messages).
- `horaire` : delivery time (format `HH:MM` or `HH:MM:SS`).
- `type` : `message` or `decompte`.
- `emetteur` : message author.
- `destinataire` : recipient role(s) (or `tous` for broadcast). *Support for multi-recipient messages with line breaks.*
- `stimuli` : message content.
- `reaction attendue` *(optional)* : expected team response.
- `commentaire` *(optional)* : note for the animator.
- `livrable` *(optional)* : expected deliverable (press release, report, etc.).

**Supported types:**
- `message` : internal message sent to designated roles.
- `decompte` : countdown window (real-time counter for the exercise).

### 2. **PMS** (tweets) — *Optional, requires `ENABLE_PMS=true`*
The Excel file `pms.xlsx` must contain at least the following columns:

- `horaire` : delivery time (format `HH:MM` or `HH:MM:SS`).
- `emetteur` : tweet author (simulated Twitter account).
- `stimuli` : tweet content.

---

## �� What's New (Latest Update)

### Improved Architecture
- **Separation of sources**: tweets and messages loadable from separate Excel files.
- **Dynamic role extraction**: roles are automatically extracted from message recipients.
- **Multi-recipient support**: a message can be addressed to multiple roles (with line breaks in CSV).

### Administration Interface
- Simplified interface with separate uploads for:
  - **Chronogramme** (messages + countdowns)
  - **PMS** (tweets) — optional, requires activation
- Load status display for each module.

### Timestamp Management
- Better handling of Excel formats and timezones.
- Automatic support for variable time formats (`HH:MM`, `HH:MM:SS`, etc.).

### Technical Improvements
- Pinned dependency versions (`requirements.txt`)
- Improved locking mechanism (threading) for shared structures.
- Complete i18n support with translations for new keys.
- No-cache headers to prevent SSE caching issues.

---

Complete documentation explaining how the platform works and how to prepare Excel files is available here:  
➡️ [Documentation/Documentation-en.md](Documentation/Documentation-en.md)

---

## 🚀 Installation

### 1. Prerequisites
- Python **3.9+**
- Pip and virtualenv

### 2. Local Installation
```bash
git clone https://github.com/jmousqueton/murail.git
cd murail
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Dependencies** (recommended versions):
- Flask==3.1.2
- pandas==2.3.3
- openpyxl==3.1.5
- python-dateutil==2.9.0.post0
- python-dotenv==1.2.1
- Unidecode==1.4.0

### 3. Configuration

Copy the example configuration file and adapt it:
```bash
cp env.example .env
```

Edit the `.env` file and fill in the required variables. See [env.example](env.example) for a detailed description of each variable.

**Main variables:**

```env
# Authentication (recommended: use different passwords)
ADMIN_PASSWORD=MyAdminPassword
ANIMATOR_PASSWORD=MyAnimatorPassword
OBSERVER_PASSWORD=MyObserverPassword

# Configuration
APP_ID=SIM-MURAIL
FLASK_SECRET=my-long-secret-key                # Generate: python3 -c "import secrets; print(secrets.token_hex(32))"
TZ=Europe/Paris                                # Timezone (e.g: Europe/Paris, UTC)
LANG=en                                        # Default language (fr or en)

# Scenario files
CHRONOGRAMME_FILE=Sample/chronogramme.xlsx     # Messages and countdowns
ENABLE_PMS=true                                # Enable PMS module (tweets)
PMS_FILE=Sample/pms.xlsx                       # Tweets (requires ENABLE_PMS=true)

# Optional
DEBUG=false                                    # Flask debug mode (do not enable in production)
DEMO=false                                     # Demo mode (bypass auth for demonstration)
TRACKING=                                      # Analytics code (e.g. Google Analytics)
PORT=5000                                      # Listen port (default: 5000)
```

**For more details**, see [env.example](env.example) which contains explanations for each variable.

### 4. Launch the Application
```bash
python app.py
```

The application is then available at [http://localhost:5000](http://localhost:5000).

---

## 🐳 Docker Deployment

### Option 1: Docker Compose (recommended)

The easiest way to deploy Murail:

```bash
# 1. Create a .env file with your configuration
cp env.example .env
# Edit .env and configure your passwords and settings

# 2. Launch the application
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop the application
docker-compose down
```

The application will be accessible at [http://localhost:5000](http://localhost:5000).

### Option 2: Docker Only

```bash
# 1. Build the image
docker build -t murail:latest .

# 2. Run the container
docker run -d \
  --name murail-app \
  -p 5000:5000 \
  -e ADMIN_PASSWORD=yourpassword \
  -e ANIMATOR_PASSWORD=yourpassword2 \
  -e OBSERVER_PASSWORD=yourpassword3 \
  -e FLASK_SECRET=$(python3 -c "import secrets; print(secrets.token_hex(32))") \
  -v $(pwd)/Sample:/app/Sample:ro \
  murail:latest
```

### Custom Scenarios with Docker

To use your own Excel files:

```bash
# Place your files in ./custom-scenarios/
docker-compose up -d

# Or with docker run:
docker run -d \
  -p 5000:5000 \
  -v $(pwd)/custom-scenarios:/app/custom-scenarios:ro \
  -e CHRONOGRAMME_FILE=/app/custom-scenarios/my-scenario.xlsx \
  murail:latest
```

### Health Check

Check container health:

```bash
# Via Docker
docker inspect --format='{{.State.Health.Status}}' murail-app

# Via HTTP
curl http://localhost:5000/health
```

### Production

For production deployment, consider:

- Use a reverse proxy (nginx, Traefik)
- Enable HTTPS with Let's Encrypt
- Configure strong passwords
- Disable `DEBUG=false` and `DEMO=false`
- Limit network access with firewall rules

---

## 👥 Target Audience

- **Crisis exercise organizers** (CISOs, IT Directors, trainers).
- **Communication, Legal, HR, Finance, and Technical teams** during training.
- **Animators** responsible for evaluating team reaction and coordination.

---

## Online Demo

A demonstration instance is available at:  
👉 [https://murail-demo.mousqueton.io](https://murail-demo.mousqueton.io)

In demo mode:

- **Animator** access does not require a password.
- **Observer** access does not require a password.
- **Admin** access is not available.
- Other features (Messaging, Social Media) remain accessible to test the scenario.
- This mode is designed for discovery purposes only.

---

## 🚀 Todo

- [ ] Add a **light/dark mode** (preference saved in browser)
- [ ] Ability to publish custom tweets (limited to communications role)
- [ ] Generate a PDF from **observer** notes

---

## 📜 License

Project distributed under GNU license.  
⚠️ This project is intended for **training and simulation purposes only**.

---

## 🙏 Acknowledgments

- **ANSSI** for organizing **REMPAR25**, which inspired this platform.
- All contributors who enrich large-scale cybersecurity exercises.
