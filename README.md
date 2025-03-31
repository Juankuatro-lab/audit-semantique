Outil d'Audit Sémantique SEO
Cet outil permet d'identifier les mots-clés à cibler pour un site grâce à une analyse concurrentielle, en comparant les mots-clés positionnés par rapport à ceux de ses concurrents.

Fonctionnalités
Import de fichiers de mots-clés positionnés (CSV, XLSX) depuis diverses sources comme SEMrush, Ahrefs, GSC
Configuration automatique ou personnalisée des colonnes selon la source des données
Filtrage personnalisable des données pour l'analyse concurrentielle
Génération d'un rapport Excel complet avec:

Analyse concurrentielle des mots-clés
Données détaillées pour chaque site
Visualisation des positions par site
Conditionnement par couleur des positions


Prérequis
-Python 3.8 ou supérieur
-Modules Python listés dans requirements.txt

Installation

1.Clonez ce dépôt:

git clone https://github.com/votre-utilisateur/audit-semantique-seo.git
cd audit-semantique-seo

2.Installez les dépendances:
-pip install -r requirements.txt

Utilisation
Lancement de l'application Streamlit
-streamlit run app.py

Comment utiliser l'outil

Exporter les mots-clés positionnés de plusieurs sites depuis Ahrefs, SEMrush, ou une autre source de données.
Importer les fichiers d'une même source et d'un même format dans l'application.
