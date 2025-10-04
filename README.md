# Simulation de Flux Aéroportuaire

Une application Python pour simuler le flux des passagers et des bagages dans un aéroport en fonction des vols programmés.

## 📋 Description

Ce projet permet de modéliser et simuler les arrivées des passagers et le traitement des bagages dans un environnement aéroportuaire. L'application utilise différentes distributions statistiques pour générer des scénarios réalistes et analyser les performances des systèmes de convoyage.

## ✨ Fonctionnalités

- **Simulation multi-distributions** : Uniforme, Normale, Exponentielle, Beta, Bimodale, Log-normale, Gamma, Weibull, Tri-modale, Pareto, Binomiale Négative
- **Visualisation avancée** : Graphiques interactifs des résultats de simulation
- **Gestion des données** : Connexion à une base SQLite contenant les informations des vols
- **Export des données** : Génération de fichiers CSV pour analyse externe
- **Interface paramétrable** : Configuration fine des paramètres de simulation
- **Gestion multi-sites** : Support de différents aéroports

## 🛠 Installation

### Prérequis
- Python 3.8+
- Les packages listés dans `requirements.txt`

### Installation des dépendances
```bash
pip install -r requirements.txt


### Structure des fichiers

project/
├── config.json              # Configuration principale
├── onda_config.py           # Classe de gestion de configuration
├── onda_db.py               # Gestion de la base de données
├── onda_aircraft.db         # Base de données SQLite (à créer)
├── requirements.txt         # Dépendances Python
└── README.md                # Ce fichier

🚀 Utilisation
🚀 Utilisation
Configuration initiale :

Modifiez config.json selon vos besoins
Assurez-vous que la base de données onda_aircraft.db est accessible
Lancement de l'application :

bash
python main.py  # ou le nom de votre script principal
Paramétrage :

Sélectionnez le site aéroportuaire

Choisissez la date de simulation

Configurez les paramètres globaux (plage horaire, capacité des convoyeurs, etc.)

Sélectionnez les distributions à utiliser

Exécution :
Lancez les simulations via l'interface
Visualisez les résultats en temps réel
Exportez les données si nécessaire

📊 Distributions Disponibles
+Distribution Uniforme
Approche simpliste avec arrivées équiprobables
Utile pour les benchmarks et premières approximations

+Distribution Normale (Gaussienne)
Arrivées groupées autour d'un temps moyen
Paramétrable avec moyenne et écart-type

+Distribution Exponentielle (Poisson)
Taux d'arrivée décroissant
Modélise les passagers "prévoyants"

+Distribution Beta
Flexibilité pour modéliser différents comportements
Paramètres α et β pour early-birds ou last-minute

+Distribution Bimodale
Combine deux populations : early-birds et last-minute
Très réaliste pour les flux aéroportuaires

Distributions Avancées
+Log-normale : Pour les comportements asymétriques
+Gamma : Temps d'attente avec queue longue
+Weibull : Flexibilité selon le paramètre de forme
+Tri-modale : Trois pics distincts d'arrivées
+Pareto : Phénomènes 80/20 avec queues lourdes
+Binomiale Négative : Comptages avec surdispersion

⚙️ Configuration
Le fichier config.json permet de configurer :

Paramètres de base : Chemin BD, site par défaut, date
Paramètres temporels : Plages horaires, pas de simulation
Bagages : Poids moyen, dimensions maximales
Convoyeurs : Capacités de traitement, limites physiques
Distributions : Paramètres par défaut pour chaque modèle

📁 Base de Données
La base de données SQLite doit contenir les tables :
aircraft : Informations sur les vols
compagnies : Informations sur les compagnies aériennes

CREATE TABLE aircraft (
    Site TEXT,
    Sens TEXT,
    NumVol TEXT,
    Compagnie TEXT,
    TypeAvion TEXT,
    DateHeurePrevue DATETIME,
    PAXpayants INTEGER
);

CREATE TABLE compagnies (
    compagnies TEXT,
    zone TEXT,
    caroussel INTEGER
);

📈 Résultats et Analyse
L'application génère :

Graphiques temporels des arrivées
Statistiques de performance des convoyeurs
Analyses de congestion et goulots d'étranglement
Données exportables pour analyses complémentaires

🤝 Contribution
Les contributions sont les bienvenues ! Pour contribuer :

Forkez le projet

Créez une branche pour votre fonctionnalité
Committez vos changements
Pushez vers la branche
Ouvrez une Pull Request

📄 Licence
Ce projet est développé dans le cadre d'un stage à l'ENAC.

👤 Auteur
Chama EL KHEMSANI
Élève à l'ENAC (École Nationale de l'Aviation Civile)
Version 1.0 - 2025

🙏 Remerciements
ENAC pour l'encadrement et les ressources

Équipe pédagogique pour le support technique

Contributeurs et testeurs

text

Ce README fournit une documentation complète couvrant :
- L'installation et la configuration
- Les fonctionnalités principales
- Les différentes distributions statistiques disponibles
- La structure du projet
- Les instructions d'utilisation
- Les informations pour les contributeurs


