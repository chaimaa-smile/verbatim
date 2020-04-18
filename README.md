# Verbatim

Projet d'analyse des données flair'soo contenu dans une application SugarCrm

* Documentation : https://support.sugarcrm.com/Documentation/Sugar_Versions/9.3/Sell/Application_Guide/
* Cours d'analyse de donnée non supervisé (clustering) : http://cedric.cnam.fr/vertigo/Cours/ml/
* Cours d'analyse de donnée supervisé (prediction, classification) : http://cedric.cnam.fr/vertigo/Cours/ml2/

# Librairies Python

* analyse FullText
  * whoosh : index full-text python
* analyse de données
  * scikit-learn : analyse de données
  * gensim : model d'analyse de texte
  * matplotlib : visualisation graphique des données
  * seaborn : visualisaion graphique des données statistiques
  * pandas : manipulation de datasets
* utilitaire
  * mysql-connector-python : connecteur python mysql
* reseaux de neuronnes :
  * keras : surchouche exploitant les librairies TensorFlow, Theano, CNTK

# Installation

Python3.7

## Avec pip

```sh
pip install -r requirements.txt
```

## Avec pipenv

```sh
pipenv install Pipfile
```

# Jupyter

Snipet de code python sous forme de notebook jupyter pour prototypage.

* AccountFeatureEngineering.ipynb : Processus de feature engineering du dataset Account
* ExtractVerbatimDataset.ipynb : Extrait des accounts, leads et verbatims de mysql vers slite3
* LeadFeatureEngineering.ipynb : Processus de feature engineering du dataset Lead
* LeadHeatMap.ipynb : Produit la heatmap de corrélation du dataset Lead (verbatim + converted, description + converted, status + converted, date + converted)
* LeadScoring.ipynb : Score un model d'analyse de Lead en fonction de la metric accuracy et log-loss
* TrainDoc2VecVerbatim.ipynb : Entraine un model Doc2Vec sur les verbatims (pas efficace)
* TrainDoc2VecWikiFR.ipynb : Entraine un model Doc2Vec sur le corpus WikipediaFR
* Word2VecExample.ipynb : Exemple de manipulation sur les word embeddings

# Data

Répertoire contenant :

* datasets : fichiers temporaires non versionnés utilisés pendant le traitement des datasets 
* models : models de prédiction pré-entrainés
* query : fichiers temporaires de la recherche full-text

# Full Text Query

Rechercher les clients dont une liste de mot clés sont fortement présents dans leurs verbatims.

* Moteur Full Text : https://whoosh.readthedocs.io/en/latest/index.html

## Query Tool

```
python query.py --help

usage: verbatim <command> [<args>]

The most commonly used verbatim commands are:
   extract     Extract verbatim from sugarcrm into a verbatim database
   index       Index verbatim from a verbatim database into an Index
   score       Update verbatim database with matching score of a query against the Index
   read        Read the most relevant verbatim from a verbatim database
   query       Query the most relevant verbatim from sugarcrm

Query most relevant verbatim

positional arguments:
  command     Subcommand to run

```

```
python query.py query -m mysql_conf -n 5 -f minimal "Talend WSO2 BigData"

[
    {
        "refid": "52b530c0-de5c-0773-7dc1-44a1414d9839",
        "type": "Accounts",
        "score": 66.59398389681378
    },
    {
        "refid": "bc966719-d2e9-0260-1102-51755b27d95b",
        "type": "Leads",
        "score": 66.1379663439615
    },
    {
        "refid": "8689bfb5-323d-b011-c3f1-5052fc49d2df",
        "type": "Leads",
        "score": 54.754410022460554
    },
    {
        "refid": "5a108ee1-e08a-77fb-a10e-543274f28cb8",
        "type": "Leads",
        "score": 40.43749586431097
    },
    {
        "refid": "38061ba1-cff6-2706-eb18-4ebb7a97a7bc",
        "type": "Accounts",
        "score": 39.464718307611996
    }
]
```

* extract : export des verbatims (notes, meetings, calls) d'une base mysql dabs une base sqlite
* index : import des verbatims dans un index (moteur full text whoosh)
* score : scoring des verbatims contre une requete
* read : recherche des verbatims les plus pertinents groupés par client
* query : macro fonction qui appelle toutes les fonctions précedentes

## Perspectives d'améliorations

* analyser les verbatims associés aux client retournés par la requête pour determiner de nouveaux mot clé ajouter à la requête
* remplacer le scoring par une mesure de la distance entre le vecteur de la chaine de caractères de la requête et le vecteur du verbatim
* remplacer l'index Whoosh par un elastic-search

# Prediction

Determiner la probabilité de conversion d'un prospect en client.

## Doc Embedding

Vectoriser un document texte.
Permet d'incorporer les verbatims du prospect au model de classification.

* Word Embedding
  * https://www.youtube.com/watch?v=gQddtTdmG_8
  * https://papers.nips.cc/paper/5021-distributed-representations-of-words-and-phrases-and-their-compositionality.pdf
* Doc Embedding
  * https://cs.stanford.edu/~quocle/paragraph_vector.pdf
  * https://radimrehurek.com/gensim/auto_examples/tutorials/run_doc2vec_lee.html#sphx-glr-auto-examples-tutorials-run-doc2vec-lee-py
* Datasets corpus wikipedia : https://dumps.wikimedia.org/frwiki/
* Gensim
  * https://pypi.org/project/gensim/
  * https://radimrehurek.com/gensim/index.html
* Model training
  * WordEmbeding pre trained : https://github.com/RaRe-Technologies/gensim-data
  * Doc Embedding Wikipedia Tutorial : https://markroxor.github.io/gensim/static/notebooks/doc2vec-wikipedia.html

## Model Doc2Vec

model pré-entrainé : data/models/wikifr_doc2vec.model

* model entrainé sur le corpus wikipedia fr https://dumps.wikimedia.org/frwiki/latest/frwiki-latest-pages-articles.xml.bz2
* paramètres 
  * dm=1
  * dm_mean=1
  * vector_size=100
  * min_count=19
  * epochs=10

## Datasets

### Accounts

| refid (Text) | date_entered (Date) | date_modified (Date) | name (Text) | type (Set) | industry (Set) | description (Text) |
| ---      |  ------  |  ------  | ------- |  ------  |  ------  | ---------:|
| 1000d0f5-be69-f406-0189-44a141e1d93e | 2006-06-27 14:32:17 | 2016-02-11 00:45:01 | exemple | None | None | exemple description |

transformation :
* vectorization des dates : Date -> Vector(Year, Month, Day)
* vectorization de la description (DocEmbedding) :  Text ->  Vector(x1, ..., xn)
* concatenation des verbatims et vectorization(DocEmbedding) :  Text ->  Vector(x1, ..., xn)
* categorization du type : {} -> OneHotVector()
* categorization industry : {} -> OneHotVector()
* elimination de l'attribut refid et name

Type :
* {None} : {Vide, None, 'X'} 
* Analyst
* Competitor
* Customer
* Integrator
* Other
* Partner
* Press
* Prospect
* Provider
* Reseller
* Supplier

Industry :
* {None} : {Vide, None} 
* Apparel
* Banking
* Biotechnology
* Chemicals
* Communications
* Construction
* Consulting
* Education
* Electronics
* Energy
* Engineering
* Entertainment
* Environmental
* Finance
* Government
* Healthcare
* Hospitality
* Insurance
* Machinery
* Manufacturing
* Media
* Not For Profit
* Other
* Recreation
* Retail
* Shipping
* Technology
* Telecommunications
* Transportation
* Utilities

### Leads

| refid (Text) | account_refid (Text) | date_entered (Date) | date_modified (Date) | title (Text) | converted (Boolean) | status (Set) | description (Text) |
| ---      |   ---      |  ------  |  ------  | ------- |  ------  |  ------  | ---------:|
| 1000d0f5-be69-f406-0189-44a141e1d93e | 2740dhgf-jk41-gh56-1425-45da18e14f3l  | 2006-06-27 14:32:17 | 2016-02-11 00:45:01 | exemple | True | None | exemple description |

transformation :
* vectorization des dates : Date -> Vector(Year, Month, Day)
* vectorization de la description (DocEmbedding) :  Text ->  Vector(x1, ..., xn)
* concatenation des verbatims et vectorization(DocEmbedding) :  Text ->  Vector(x1, ..., xn)
* categorization du status : {} -> OneHotVector()
* elimination de l'attribut refid, account_refid et title

Status :
* Converted
* Dead
* Disqualified
* Evanglist
* Identified
* Immediate
* In Process
* Inexploitable
* Lead
* New
* NotApplicable
* NotInteresting
* Recycled
* SQL

## Analyse du dataset Lead

### Correlation Matrix HeatMap

![Correlation Matrix HeatMap](jupyter/lead_corr_matrix_verbatim_converted.png?raw=true "CorrelationMatrix verbatim + converted heatmap")
![Correlation Matrix HeatMap](jupyter/lead_corr_matrix_status_converted.png?raw=true "CorrelationMatrix status + converted heatmap")
![Correlation Matrix HeatMap](jupyter/lead_corr_matrix_other_converted.png?raw=true "CorrelationMatrix date + converted heatmap")
![Correlation Matrix HeatMap](jupyter/lead_corr_matrix_description_converted.png?raw=true "CorrelationMatrix description + converted heatmap")

* On voit une legère correlation entre les valeurs du vecteur verbatim et l'attribut converted
* On voit une legère correlation entre certaines valeurs du vecteur status et l'attribut converted
* On voit une legère correlation entre certaines valeurs du vecteur date et l'attribut converted
* On ne voit pas de correlation entre les valeurs du vecteur description et l'attribut converted

### Model de prédiction

* Famille de modèle : Knn
* HyperParametres : {'n_neighbors': integer, 'weights': ('uniform', 'distance')}
* Scoring :
  * Accuracy mesure de la précision entre 0 et 1 (1 score idéal) 
  * Log-Loss mesure de l'erreur de classification entre 0 et 1 (0 score idéal) (a n'utiliser que pour les modèles à 2 classes)
  * Cross-Entropy mesure de l'erreur de classification entre 0 et 1 (0 score idéal) (a n'utiliser que pour les modèles multi classes)
* GridSearch : Fait varier les hyperparamètres d'une famille de modèle afin de determiner la meilleur configuration
* CrosValidation : Découpe un dataset en plusieurs datasets d'entrainement et de validation et calcule les scores moyens

### Résultat

| params | mean_test_accuracy | std_test_accuracy | rank_test_accuracy | mean_test_log_loss | std_test_log_loss | rank_test_log_loss |
| ---    |   ---              |  ------           |  ------            | -------            |  ------           |          ---------:|
{'n_neighbors': 19, 'weights': 'distance'} | 0.990855 | 0.000118 | 1 | 0.315863 | 0.004069 | 1
{'n_neighbors': 20, 'weights': 'distance'} | 0.990850 | 0.000125 | 2 | 0.316033 | 0.004303 | 2
{'n_neighbors': 22, 'weights': 'distance'} | 0.990840 | 0.000110 | 3 | 0.316372 | 0.003807 | 3
{'n_neighbors': 21, 'weights': 'distance'} | 0.990835 | 0.000113 | 4 | 0.316541 | 0.003888 | 4
{'n_neighbors': 23, 'weights': 'distance'} | 0.990820 | 0.000104 | 5 | 0.317050 | 0.003598 | 5
{'n_neighbors': 24, 'weights': 'distance'} | 0.990781 | 0.000100 | 6 | 0.318406 | 0.003459 | 6
{'n_neighbors': 19, 'weights': 'uniform'} | 0.990492 | 0.000183 | 7 | 0.328410 | 0.006335 | 7
{'n_neighbors': 20, 'weights': 'uniform'} | 0.990452 | 0.000122 | 8 | 0.329766 | 0.004222 | 8
{'n_neighbors': 21, 'weights': 'uniform'} | 0.990452 | 0.000135 | 9 | 0.329766 | 0.004675 | 9
{'n_neighbors': 23, 'weights': 'uniform'} | 0.990438 | 0.000170 | 10 | 0.330275 | 0.005888 | 10
{'n_neighbors': 22, 'weights': 'uniform'} | 0.990433 | 0.000143 | 11 | 0.330444 | 0.004955 | 11
{'n_neighbors': 24, 'weights': 'uniform'} | 0.990403 | 0.000141 | 12 | 0.331461 | 0.004884 | 12

* rank_test_accuracy : rang dans la catégorie des précisions moyennes les plus grandes
* mean_test_accuracy : précision moyenne du modèle sur toutes les parties de la cross-validation
* std_test_accuracy : écart type de la précision moyenne du modèle sur toutes les parties de la cross-validation
* rank_test_log_loss : rang dans la catégorie des log-loss moyennes les plus basses
* mean_test_log_loss : log-loss moyenne du modèle sur toutes les parties de la cross-validation
* std_test_log_loss : écart type de la log-loss moyenne du modèle sur toutes les parties de la cross-validation

Avec une précision de 99%, je suspect un fort biais de classification.
Il serait bon de verifier les proportions de l'attribut converted sur le dataset Lead

## Perspectives d'améliorations

* entrainer un nouveau model Doc2Vec en changeant l'algorithme d'approximation par DBOW (Distributed Bag Of Words)
  * dm=0
  * dbow_words=1
  * vector_size=200
  * min_count=19
  * epochs=10
* le dataset Lead n'est pas simplement composé de prospect, il faudrait le nettoyer
* la description des leads ne semble pas etre corrélée au resultat de la prediction il faudrait retirer l'attribut du dataset
* aggreger les status qui ne corrélent pas avec l'attribut à prédire
* tester d'autres familles de modèles (RegressionLogistic, SupportVectorMachine, Réseaux de neuronnes)
