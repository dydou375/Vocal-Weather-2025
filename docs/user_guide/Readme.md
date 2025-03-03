# Guide de l'utilisateur pour l'application de prévision météorologique (Open-Meteo)

Bienvenue dans l'application de prévision météorologique (Open-Meteo). Ce guide vous aidera à configurer et utiliser l'application pour obtenir des prévisions météorologiques précises.

## Prérequis

Avant de commencer, assurez-vous d'avoir les éléments suivants :
- Un ordinateur avec une connexion Internet.
- Python installé sur votre machine (version 3.6 ou supérieure).
- Un microphone si vous souhaitez utiliser la commande vocale.

## Installation

1. Clonez le dépôt GitHub de l'application :
   ```bash
   git clone https://github.com/votre-utilisateur/votre-repo.git
   ```

2. Accédez au répertoire du projet :
   ```bash
   cd Vocal_Weather/Vocal-Weather-2025
   ```

3. Installez les dépendances requises :
   ```bash
   pip install -r requirements.txt
   ```

4. Créez un fichier `.env` à la racine du projet et ajoutez vos variables d'environnement (si nécessaire).

## Lancement de l'application

1. Démarrez le backend FastAPI :
   ```bash
   uvicorn app.main:app --reload
   ```

2. Démarrez l'application Streamlit :
   ```bash
   streamlit run app/streamlit/app.py
   ```

## Utilisation de l'application

### Mode de commande

Lorsque vous ouvrez l'application, vous pouvez choisir entre deux modes de commande :
- **Enregistrement par micro** : Utilisez votre voix pour donner des commandes.
- **Manuelle** : Entrez les informations manuellement.

### Commande vocale

1. Sélectionnez "Enregistrement par micro".
2. Cliquez sur "Enregistrer la commande vocale".
3. Parlez clairement pour donner votre commande (par exemple, "Prévisions pour Paris").
4. La transcription de votre commande s'affichera. Vérifiez qu'elle est correcte.
5. Cliquez sur "Envoyer la commande vocale" pour obtenir les prévisions météorologiques.

### Commande manuelle

1. Sélectionnez "Manuelle".
2. Entrez le nom de la ville pour laquelle vous souhaitez obtenir les prévisions.
3. Cliquez sur "Envoyer la commande" pour obtenir les prévisions météorologiques.

### Affichage des résultats

Les résultats des prévisions peuvent être affichés sous trois formes :
- **Graphique** : Affiche les prévisions sous forme de graphiques interactifs.
- **Tableau** : Affiche les prévisions sous forme de tableau.
- **Texte** : Affiche les prévisions sous forme de texte détaillé.

## Résolution des problèmes

- **Erreur de décodage JSON** : Assurez-vous que le backend FastAPI est en cours d'exécution.
- **Ville introuvable** : Vérifiez l'orthographe de la ville et réessayez.

## Support

Pour toute question ou problème, veuillez contacter notre support technique à support@open-meteo.com.

Merci d'utiliser notre application de prévision météorologique !
