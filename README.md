# QCM Sécurisé – Projet LPASSR

Application web Flask pour évaluation sécurisée en culture informatique.

## Fonctionnalités

### Étudiant
- Inscription / Connexion sécurisée (bcrypt)
- QCM : 10 questions aléatoires depuis un pool de 100+
- 30 secondes par question avec minuterie stricte
- Mode plein écran obligatoire
- Anti-triche : détection changement d'onglet, blocage copier-coller / F12
- Résultats détaillés avec corrections
- Historique des tentatives

### Administrateur
- Tableau de bord avec statistiques (Chart.js)
- CRUD complet utilisateurs et questions
- Filtres par catégorie / difficulté / recherche
- Export CSV des résultats et questions
- Visualisation des incidents de triche
- Questions les plus ratées

## Installation

### 1. Cloner le dépot git hub

```bash
git clone "https://github.com/hlecomte/Python_projet_2/"
cd Python_projet_2
```

### 2. Créer l'environnement virtuel

```bash
python -m venv venv
source venv/bin/activate       # Linux / macOS
venv\Scripts\activate          # Windows
```

### 3. Installer les dépendances

```bash
pip install -r requirements.txt
```

### 4. Initialiser la base de données (100+ questions)

```bash
python seed.py
```

### 5. Lancer l'application

```bash
python app.py
```

Accès : http://localhost:5000

## Comptes par défaut

| Rôle       | Nom d'utilisateur | Mot de passe   |
|------------|-------------------|----------------|
| Admin      | `admin`           | `Admin1234!`   |
| Étudiant   | `etudiant`        | `Etudiant1234!`|

## Stack technique

| Composant    | Technologie                          |
|--------------|--------------------------------------|
| Back-end     | Python 3 / Flask 3                   |
| ORM          | Flask-SQLAlchemy (SQLite)            |
| Auth         | Flask-Login + bcrypt                 |
| Formulaires  | Flask-WTF (protection CSRF)          |
| Front-end    | Bootstrap 5 + Bootstrap Icons        |
| Graphiques   | Chart.js                             |
| Anti-triche  | JavaScript (Fullscreen API, visibilitychange, keydown) |

## Structure du projet

```
.
├── app.py                  # Point d'entrée Flask
├── config.py               # Configuration
├── models.py               # Modèles SQLAlchemy
├── forms.py                # Formulaires WTForms
├── seed.py                 # Peuplement BDD (100+ questions)
├── requirements.txt
├── routes/
│   ├── auth.py             # Inscription / Connexion / Déconnexion
│   ├── student.py          # QCM, résultats, historique
│   └── admin.py            # Tableau de bord admin, CRUD
├── templates/
│   ├── base.html
│   ├── auth/               # login.html, register.html
│   ├── student/            # dashboard, qcm, result, history
│   ├── admin/              # dashboard, users, questions, stats
│   └── errors/             # 403, 404, 500
└── static/
    ├── css/style.css
    └── js/qcm.js           # Anti-triche JavaScript
```

## Sécurité implémentée

- Mots de passe hachés avec **bcrypt**
- Protection **CSRF** sur tous les formulaires (Flask-WTF)
- Validation stricte côté serveur
- Sessions sécurisées (httponly, samesite)
- Vérification du temps total côté serveur (détection contournement timer)
- Journalisation des incidents de triche en base de données
- Contrôle d'accès par rôle (étudiant / admin)
- Protection XSS via échappement Jinja2

## Catégories de questions

- **Réseaux** (25 questions) : OSI, TCP/IP, protocoles, adressage
- **Sécurité** (25 questions) : chiffrement, attaques, bonnes pratiques
- **Système** (25 questions) : Linux, processus, système de fichiers
- **Programmation** (25 questions) : algorithmes, POO, structures de données
- **Base de données** (25 questions) : SQL, normalisation, transactions
