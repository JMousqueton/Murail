# 📄 Documentation

## ⚙️ Completing the Scenario Excel File

This Excel file defines the **stimuli** that will be automatically triggered during the simulation (tweets, messages, or countdowns).

Each row corresponds to one event.

---

### 🗂️ Mandatory Columns

#### `id`
- **Only for messages.**
- Used to identify and order messages.
- Recommended format: **simple incremental numbering** (`001`, `002`, `003`, …).
- Example: `001` for the first message, `002` for the second, etc.
- **Note:** for tweets or countdowns, leave this cell empty.

---

#### `Horaire`
- Time when the event is triggered, in **HH:MM** format.
- The current date is automatically used.
- Example: `09:15` will trigger the event at 9:15 a.m. (Paris time).

---

#### `Type`
- Type of stimulus expected:
  - `tweet` → post on the social media feed.
  - `message` → message in the internal mailbox.
  - `decompte` → display of a countdown timer (duration in minutes defined in `Stimuli`).

---

#### `Emetteur` (Sender)
- **Required** for `tweet` and `message`.
- Name of the person or entity sending it.
- Example: `Management`, `CISO`, `Le Monde Newspaper`.

If `Emetteur` is set to `aléatoire` (random), a pseudonym will be randomly chosen from the `tweet.txt` file in the `static/data` directory.
If an image file named `Emetteur.png` or `.jpg` exists in `static/images/tweet/`, it will be used as the avatar.

---

#### `Destinataire` (Recipient)
- **Only for messages.**
- Corresponds to the target role of the message:
  - `Communication`
  - `Decision`
  - `IT`
  - `Legal / Finance`
  - `Human Resources`
  - `Business`
  - or `All` for a general message.

---

#### `Stimuli`
- Content of the event.
- For a `tweet` → tweet text (hashtags allowed).
  - **Tip:** you can include an image using the syntax:
    ```
    [img filename.png]
    ```
    Images must be stored in the **`static/images/`** folder of the project.
    👉 They can be **uploaded directly via the admin interface** (*Upload image* section).
    Example: `New leak revealed! [img leak.png]`
- For a `message` → email body text.
- For a `decompte` → countdown duration in minutes (example: `15`).

---

### 📝 Optional Columns

These columns are intended for the **facilitator/animator** role only.

#### `Réaction attendue` (Expected Reaction)
- Indicates the desired response from participants.
- Example: *"Notify the communication team."*

#### `Commentaire` (Comment)
- Additional information for the exercise facilitators.

#### `Livrable` (Deliverable)
- Indicates an expected document.
- Example: *"Write a press release."*

---

### ✅ Example Table

| id   | Horaire | Type     | Emetteur      | Destinataire   | Stimuli                                   | Réaction attendue                  | Commentaire              | Livrable               |
|------|----------|-----------|---------------|----------------|-------------------------------------------|------------------------------------|--------------------------|------------------------|
|      | 09:00    | tweet     | News Journal  |                | #Cyberattack in progress! [img fuite.png]  | Analyze media impact               | First public tweet       |                        |
| 001  | 09:05    | message   | CISO          | IT             | Incident detected on server X             | Isolate the server                 | Technical data           | Analysis report        |
|      | 09:10    | decompte  |               |                | 15                                        | Wait for the countdown to end      | 15-min simulation pause  |                        |
| 002  | 09:20    | message   | Management    | Communication  | Prepare an official statement             | Draft internal communication       | Check text consistency   | Internal statement     |

---

👉 With this structure, the simulation knows **what to trigger, when, and for whom**.

---

## 🖥️ User Interface

The application offers several web interfaces that allow participants and facilitators to follow the exercise in real time.

---

### 📌 Home Page (`/`)

- **Global view** of the exercise.
- Displays:
  - Links to the various interfaces (Social Media, Messaging, Observer, Administration).
  - Scenario status (loaded or empty).
  - The **last 5 triggered events** (messages only).
- Serves as the main entry point for participants.

![Home](img/accueil.png)

---

### 🐦 Social Media (`/socialmedia`)

- Simulates a **Twitter-like feed**.
- Features:
  - Displays **tweets** defined in the scenario.
  - Supports **hashtags** → trends update in real time in the right column.
  - Supports **images** using `[img name.png]`.
  - Dynamic display of **retweet and like counts**, which increase automatically.
  - Filter by active hashtag → clicking a trend topic filters the feed.
- A clock (Paris time) is visible in the top right.

![Social Media](img/mediassociaux.png)

---

### ✉️ Messaging (`/messagerie`)

- Simulates an **internal mailbox** (like Outlook or Webmail).
- Features:
  - Each participant selects their **role** (Communication, Decision, IT, HR, etc.).
  - The inbox displays only **messages addressed to that role**.
  - Messages can be **opened and viewed**.
  - Each message can be marked as **processed** ✅ (stored locally, persistent per role).
  - History of the last 100 messages is loaded.
  - Real-time updates via **SSE (Server-Sent Events)**.

![Messaging](img/messagerie.png)

---

### 🔎 Facilitator (`/animateur`)

- Restricted to **facilitators/controllers**.
- Access protected by password (auto-filled in demo mode).
- Features:
  - Overview of all **broadcasted messages**.
  - The **last 5 messages**.
  - The **next 2 scheduled messages**.
  - Displays **expected reactions** and **comments** from the Excel file.

![Facilitator](img/animateur.png)

---

### 👁️ Observer (`/observateur`)

- Restricted to **observers/evaluators** (password required).
- Features:
  - Focused view of **stimuli (messages)** in the exercise.
  - The **next message** appears at the top, greyed out until its time.
  - **Past messages** are listed in reverse chronological order.
  - For each stimulus, the observer can:
    - Give a **quick rating** (👍 / 👎).
    - Add a **free-text comment**.
  - Notes are **saved locally** in the browser.
  - Option to **export** observations to **JSON** or **CSV** for analysis/debriefing.

![Observer](img/observateur.png)

---

### ⚙️ Administration (`/admin`)

- Restricted to **facilitators** (password required).
- Features:
  - **Load a scenario** (Excel file).
  - View past and upcoming events.
  - **Upload images** (usable in tweets via `[img name.png]`).
  - Indicator showing whether a scenario is loaded.

![Admin](img/admin.png)

---

### ⏳ Countdown

- When the scenario contains a **`decompte`** stimulus:
  - Player interfaces (Messaging and Social Media) automatically switch to a **full-screen countdown**.
  - The home page also displays the timer.
  - The timer appears with a red glow effect.
  - When the countdown ends, the Messaging and Social Media interfaces return to normal automatically.

![Countdown](img/decompte.png)

---

## ⚙️ `.env` File

The `.env` file configures the application without modifying the code.
It contains sensitive parameters (passwords, secrets, file paths).

### Variable Details

- **`ADMIN_PASSWORD`** – Password for the **Administration** interface.
- **`OBSERVER_PASSWORD`** – Password for the **Observer** interface.
- **`ANIMATOR_PASSWORD`** – Password for the **Facilitator** interface.
- **`APP_ID`** – Unique ID for the simulation instance (useful to separate environments).
- **`FLASK_SECRET`** – Secret key used by Flask for managing user sessions (⚠️ must be unique and complex).
- **`SCENARIO_XLSX`** – Path to the Excel file containing the **timeline** (default: `./Sample/chronogramme.xlsx`).
- **`DEMO`** – If `true`, enables **demo mode** (Observer password auto-filled).
- **`TRACKING`** – Optional analytics script (e.g., **Matomo**, Google Analytics).
  - The content is injected at the bottom of each page (`{{ TRACKING | safe }}`).
  - Example: internal Matomo tracking script.

👉 **Security tip:** never share the real `.env` content publicly (especially passwords or `FLASK_SECRET`).

---

### 🧪 Demo Mode

- A demo instance is available:
  👉 [https://murail-demo.mousqueton.io](https://murail-demo.mousqueton.io)
- In this mode:
  - The Observer password is auto-filled.
  - Allows easy testing without local setup.
