
# **README — Solution d’Automatisation du SAV à partir de Tweets Clients**

## 📌 **Nom du projet : SAV-Free – Analyse automatisée des tweets clients**

Cette solution a été développée dans le cadre du Bloc C2/C3 et vise à automatiser l’analyse des interactions clients sur Twitter afin d’aider le service client de Free à :

* détecter automatiquement les plaintes, suggestions, questions et remerciements,
* analyser le sentiment réel (y compris ironie),
* identifier les priorités et risques (urgence, résiliation),
* fournir un dashboard opérationnel pour les agents, managers et analystes,
* proposer un fil public inspiré de Twitter pour la visualisation des posts.

Le projet repose sur un pipeline complet : ingestion → nettoyage → NLP → LLM (Mistral) → enrichissement → dashboards.

---

## 👥 **Équipe projet**

| Nom                             | Rôle                | Mission principale                                                                                                   |
| ------------------------------- | -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Émilienne Ekassi**     | Data Engineer        | Conception du pipeline technique, nettoyage et transformation des données, orchestration complète du traitement.   |
| **Kevine FIANGUEU SIABO** | Data Scientist (NLP) | Développement des règles NLP, conception des prompts LLM, classification automatique, détection du sarcasme.      |
| **Jordan DJILLA**        | Product Owner        | Recueil du besoin, priorisation des fonctionnalités, validation continue et communication avec le client.           |
| **Mohamed ABOU ABDILLAH**   | DevOps / MLOps       | Gestion environnement, intégration, automatisation, industrialisation du pipeline et optimisation des performances. |

---

## 🏗️ **Architecture globale de la solution**

```
tweets.csv  →  Pipeline Data  →  NLP + LLM (Mistral)  
              →  tweets_prepared.csv  
              →  tweets_enriched.csv  
              →  Dashboards multi-profils  
              →  Fil public type Twitter
```

La solution comporte **4 modules principaux** :

1. **Pipeline Data Engineer**
2. **NLP & LLM (Mistral)**
3. **Dashboards Streamlit internes (Agent, Manager, Analyste, Admin)**
4. **Fil public (lecture des tweets façon réseau social)**

---

## ⚙️ **1. Pipeline de données**

Le pipeline complet est orchestré dans :

```
backend/data_pipeline/enrichment_pipeline.py
```

Il comporte les étapes suivantes :

### 🔹 **Ingestion**

Chargement du fichier `tweets.csv` depuis le dossier  *raw* .

### 🔹 **Nettoyage / Structuration**

* suppression URLs, mentions, hashtags
* normalisation du texte
* identification des retweets, citations, réponses
* détection des comptes officiels Free
* création de `tweets_prepared.csv`

### 🔹 **NLP classique**

* détection des mots de panne
* scoring de sentiment préliminaire
* identification ironie / urgence / résiliation
* extraction features utilisées par le LLM

### 🔹 **Enrichissement par LLM (Mistral)**

* classification automatique :
  * Intent (complaint, suggestion…)
  * Type de plainte (fibre, mobile, SAV…)
  * Sentiment
  * Sarcasme
  * Priorité
  * Risque de résiliation
* correction des faux positifs/negatifs avec règles métier
* export final → `tweets_enriched.csv`

---

## 📊 **2. Dashboards Streamlit**

L’application inclut **4 espaces internes** et  **1 espace public** .

### 🔹 **1. Agents (1_Agent.py)**

* Liste des plaintes
* Filtrage par priorité, type, sentiment
* Possibilité de mettre à jour l’état du ticket :
  * « Nouveau », « En cours », « Résolu »

### 🔹 **2. Manager (2_Manager.py)**

* KPI opérationnels
* Nombre de plaintes
* Priorités critiques
* Tendance dans le temps
* Analyse du risque de résiliation

### 🔹 **3. Analyste (3_Analyst.py)**

* Vision globale sur les 6 375 tweets
* Graphiques professionnels (camembert, barres, timeline)
* Répartition par intent, sentiment, type de plainte
* Rapport exportable

### 🔹 **4. Administrateur (4_Admin_Upload_CSV.py)**

* Upload du fichier brut
* Lancement du pipeline complet
* Indicateur si les fichiers préparés / enrichis existent déjà
* KPI immédiats + rapport synthétique

### 🔹 **5. Fil Public (5_Public_Feed.py)**

* Simulation d’une timeline Twitter
* Affichage des posts, retweets et citations
* Affichage des commentaires à l’ouverture
* Recherche + pagination
* Style proche d’un réseau social réel

---

## 🧠 **3. Technologies utilisées**

* **Python 3.11**
* **Pandas / NumPy** — traitement de données
* **Streamlit** — interfaces
* **Mistral API (mistral-small-latest)** — classification LLM
* **Regex + NLP maison** — détection heuristique
* **GitHub** — versioning
* **dotenv** — gestion des variables sensibles
* **Altair / Matplotlib** — visualisations

---

## 🗂️ **Structure du projet**

```
solution_Sav_Free/
│
├── backend/
│   ├── data_pipeline/
│   │     ├── ingestion.py
│   │     ├── cleaning_service.py
│   │     ├── nlp_basic_service.py
│   │     ├── llm_client.py
│   │     ├── classification.py
│   │     └── enrichment_pipeline.py
│   │
│   └── analytics/
│         ├── kpis_analyst.py
│         └── report_builder.py
│
├── app_service/
│   ├── Home.py
│   ├── pages/
│   │    ├── 1_Agent.py
│   │    ├── 2_Manager.py
│   │    ├── 3_Analyst.py
│   │    ├── 4_Admin_Upload_CSV.py
│   │    └── 5_Public_Feed.py
│
├── data/
│   ├── raw/tweets.csv
│   ├── processed/tweets_prepared.csv
│   └── processed/tweets_enriched.csv
│
└── .env
```

---

## **Installation**

```
git clone https://github.com/tonProjet/sav-free
cd sav-free
pip install -r requirements.txt
```

Créer un fichier `.env` :

```
MISTRAL_API_KEY=TON_API_KEY
MISTRAL_MODEL=mistral-small-latest
```

Lancer l’application :

```
streamlit run app_service/Home.py
```

---

## **Objectif final**

La solution permet à Free de :

* comprendre automatiquement les tweets clients,
* prioriser les urgences,
* détecter les plaintes réelles même ironiques,
* suivre son service client,
* afficher un dashboard professionnel multi-profils,
* disposer d’une timeline publique style Twitter.

Cette architecture peut être réutilisée pour d’autres réseaux sociaux ou services clients.
