import random
import numpy as np
from copy import deepcopy
from typing import Dict, List
from datetime import datetime,date, time, timedelta
from typing import List, Dict, Optional
from collections import defaultdict
from PyQt5.QtCore import QObject, pyqtSignal
import concurrent.futures

from onda_db import DBaircraft
from onda_config import Params




class Simulate:
    def __init__(self,params ,name):
        self.params = params
        self.name=name
        self.init_db()


    def init_db(self):
        self.dbaircraft=DBaircraft(self.params.db_path)
        self.departures=self.dbaircraft.get_flights( self.params.site, self.params.date_str,self.params.compagnies,self.params.num_vols)  
        all_compagnies=self.dbaircraft.get_compagnies_info()
        departures_compagnies = list(set([flight.company for flight in self.departures]))
        self.compagnies={compagnie:all_compagnies[compagnie]  for compagnie in departures_compagnies}
        self.flights_carrousel={flight.flight_number:all_compagnies[flight.company]  for flight in self.departures}

    def init_db_compagnies(self,compagnies):
        departures_compagnies = list(set([flight.company for flight in self.departures]))
        self.compagnies={compagnie:compagnies[compagnie]  for compagnie in departures_compagnies}
        self.flights_carrousel={flight.flight_number:compagnies[flight.company]  for flight in self.departures}

    def init_db_flights(self,flights):
        self.flights_carrousel={flight.flight_number:flights[flight.flight_number]  for flight in self.departures}

    def distribution(self,departure_min,max_pax):
        pass


    def run(self):
        """
        Simule le nombre de bagages enregistrés par intervalle de temps en utilisant une distribution.
        """
        day_start=self.params.day_start
        day_end=self.params.day_end
        step_time=self.params.step_time

        random.seed(self.params.default_seed)
        np.random.seed(self.params.default_seed)

        # Convertir les heures de journée en minutes
        start_min = int(day_start.split(":")[0]) * 60 + int(day_start.split(":")[1])
        end_min = int(day_end.split(":")[0]) * 60 + int(day_end.split(":")[1])

        
        # Initialiser les dictionnaires pour compter les elements par intervalle de temps
        time_slots_vols = {}
        time_slots_voyageurs = {}
        time_slots_bagages= {}
        time_slots_enregistrements= {}
        time_slots_manutentionnaires= {}
        current_time = start_min
        while current_time < end_min:
            time_slots_vols[current_time] = []
            time_slots_voyageurs[current_time] = []
            time_slots_bagages[current_time] = []
            time_slots_enregistrements[current_time] = []
            time_slots_manutentionnaires[current_time] = []
            current_time += step_time

        
        # Traiter chaque vol
        for flight in self.departures:
            max_pax = flight.passenger_count
            departure_time = flight.scheduled_datetime
            compagnie_caroussel=self.flights_carrousel[flight.flight_number]
            hour = departure_time.hour
            departure_min = departure_time.hour * 60 + departure_time.minute
            open_time = departure_min - self.params.open_min
            close_time = departure_min - self.params.close_min

            #info pour les vols
            for slot in time_slots_vols:
                if departure_min >= slot and departure_min < slot + step_time:
                    time_slots_vols[slot].append([flight.flight_number,compagnie_caroussel])
                    break

            #info pour les enregistrements
            current_time = open_time
            while current_time < close_time:
                for slot in time_slots_enregistrements:
                   if current_time >= slot and current_time < slot + step_time:
                        time_slots_enregistrements[slot].append([flight.flight_number,compagnie_caroussel])
                        break
                current_time += step_time

            #info pour les manutentionnaires
            current_time = open_time
            while current_time < departure_min:
                for slot in time_slots_manutentionnaires:
                   if current_time >= slot and current_time < slot + step_time:
                        time_slots_manutentionnaires[slot].append([flight.flight_number,compagnie_caroussel])
                        break
                current_time += step_time

            all_arrivals=self.distribution(departure_min,open_time,close_time,max_pax)
            for arrival_time in all_arrivals:
                arrival=int(arrival_time)
                for slot in time_slots_voyageurs:
                    if arrival >= slot and arrival < slot + step_time:
                        time_slots_voyageurs[slot].append(flight.flight_number)
                        nb_bagages=random.randint(0, self.params.max_bagage)
                        if nb_bagages:
                            time_slots_bagages[slot].append([flight.flight_number,nb_bagages,compagnie_caroussel])
                        break
            
        # Préparer les données 
        times = [f"{t//60:02d}:{t%60:02d}" for t in time_slots_voyageurs.keys()]
        voyageur_liste = list(time_slots_voyageurs.values())
        bagage_liste = list(time_slots_bagages.values())
        enregistrement_liste = list(time_slots_enregistrements.values())
        manutentionnaire_liste = list(time_slots_manutentionnaires.values())
        vols_liste = list(time_slots_vols.values())
        return {"times": times, 
                "vols":vols_liste,
                "enregistrements": enregistrement_liste,
                "manutentionnaires": manutentionnaire_liste,
                "voyageurs": voyageur_liste,
                "bagages": bagage_liste
                }

    def simulate_caroussel(self,data,caroussel):
        """
        Simule le nombre de bagages enregistrés par intervalle de temps en utilisant une distribution.
        """
        bagages_sur_tapis = []
        nombre_sur_tapis = 0
        poids_sur_tapis = 0
        longueur_sur_tapis = 0
        bagages_traite_manutentionnaire = self.params.traitement * self.params.step_time 
        list_bagages_sur_tapis=[]
        list_poids_sur_tapis=[]
        list_longueur_sur_tapis=[]
        list_echec=[]
        list_poids_depasse=[]
        list_longueur_depasse=[]
        list_bagage_non_traites=[]
        for i in range(len(data["times"])):
            #print("------------------------------------------------------")
            #print("i",i)
            #print("time",data["times"][i])

            manutentionnaires=self.select_caroussel_vols( data["manutentionnaires"][i],caroussel)
            new_baggages=self.select_caroussel_bagages(data["bagages"][i],caroussel)
            bagages_sur_tapis=bagages_sur_tapis+new_baggages

            #nombre_sur_tapis_avant = sum(bagage[1] for bagage in bagages_sur_tapis)
            #print("nombre_sur_tapis-Avant",nombre_sur_tapis_avant)
            #print("nombre_manutentionnaire",len(manutentionnaires))
            #print("manutentionnaires",manutentionnaires)
            #print("Tapis",bagages_sur_tapis)
            
            bagages_sur_tapis,nb_reject=self.purge_bagages(bagages_sur_tapis,manutentionnaires)
            list_bagage_non_traites.append(nb_reject)
            for manutentionnaire in manutentionnaires:
                bagages_sur_tapis=self.retirer_bagages(bagages_sur_tapis, manutentionnaire, bagages_traite_manutentionnaire)

            nombre_sur_tapis = sum(bagage[1] for bagage in bagages_sur_tapis)
            #print("nombre_sur_tapis-Apres",nombre_sur_tapis)
            #print("nombre_traiter",nombre_sur_tapis_avant-nombre_sur_tapis)
            
            
            poids_sur_tapis = round(nombre_sur_tapis * self.params.poids_moyen_bagage, 2)
            longueur_sur_tapis = round(nombre_sur_tapis * self.params.longueur_moyenne_bagage, 2)
            #print("poids_sur_tapis",poids_sur_tapis)
            #print("longueur_sur_tapis",longueur_sur_tapis)
            
            poids_depasse = poids_sur_tapis > self.params.poids_max
            longueur_depasse = longueur_sur_tapis > self.params.longueur_max
            echec = poids_depasse or longueur_depasse
            #print("echec",echec)
            
            list_bagages_sur_tapis.append(nombre_sur_tapis)
            list_poids_sur_tapis.append(poids_sur_tapis)
            list_longueur_sur_tapis.append(longueur_sur_tapis)
            list_echec.append(echec)
            list_poids_depasse.append(poids_depasse)
            list_longueur_depasse.append(longueur_depasse)

        nombre_echec=sum(1 if(echec) else 0 for echec in list_echec)

        return {
                "times": data["times"], 
                "Bagages_sur_tapis": list_bagages_sur_tapis,
                "Poids_sur_tapis": list_poids_sur_tapis,
                "Longueur_sur_tapis": list_longueur_sur_tapis,
                "Echec": list_echec,
                "Poids_depasse": list_poids_depasse,
                "Longueur_depasse": list_longueur_depasse,
                "Bagages_rejetes":list_bagage_non_traites,
                "nombre_echec":nombre_echec
                }

    def simulate(self, data):
        """Exécute les simulations des carrousels en parallèle"""
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            # Soumettre toutes les tâches de simulation
            futures = {
                executor.submit(self.simulate_caroussel, data, i): i 
                for i in range(1, 6)
            }
            
            # Créer un dictionnaire pour stocker les résultats
            results = {}
            
            # Attendre que toutes les tâches se terminent et récupérer les résultats
            for future in concurrent.futures.as_completed(futures):
                caroussel_num = futures[future]
                try:
                    results[f"caroussel_{caroussel_num}"] = future.result()
                except Exception as exc:
                    print(f'Carrousel {caroussel_num} a généré une exception: {exc}')
                    # En cas d'erreur, créer un résultat vide
                    results[f"caroussel_{caroussel_num}"] = {
                        "times": data["times"],
                        "Bagages_sur_tapis": [0] * len(data["times"]),
                        "Poids_sur_tapis": [0] * len(data["times"]),
                        "Longueur_sur_tapis": [0] * len(data["times"]),
                        "Echec": [False] * len(data["times"]),
                        "Poids_depasse": [False] * len(data["times"]),
                        "Longueur_depasse": [False] * len(data["times"]),
                        "Bagages_rejetes": [0] * len(data["times"]),
                        "nombre_echec": 0
                    }

        # Calculer le nombre total d'échecs
        total_echecs = sum(results[f"caroussel_{i}"]["nombre_echec"] for i in range(1, 6))
        
        # Ajouter le total au dictionnaire de résultats
        results["nombre_echec"] = total_echecs
        
        return results


    def retirer_bagages(self,liste, vol, nombre_bagages):
        """
        retirer des bagages lu tapis
        """
        bagages_restants = nombre_bagages
        nouvelle_liste = []
        
        for item in liste:
            if item[0] == vol and bagages_restants > 0:
                if item[1] <= bagages_restants:
                    bagages_restants -= item[1]
                    continue  # On retire complètement cet élément
                else:
                    item[1] -= bagages_restants
                    bagages_restants = 0
                    nouvelle_liste.append(item)
            else:
                nouvelle_liste.append(item)
        
        return nouvelle_liste

    def purge_bagages(self,liste,vols):
        """
        enlever les bagages des vols déjà partis 
        """
        nouvelle_liste = []
        bagages_rejete = 0
        for item in liste:
            if item[0]  in vols:
                nouvelle_liste.append(item)
            else:
                bagages_rejete += item[1]
        return nouvelle_liste,bagages_rejete

    def select_caroussel_bagages(self,liste,caroussel):
        """
        recuperer les bagages affectés à ce caroussel
        """
        nouvelle_liste = []
        for item in liste:
            if item[2]  == caroussel :
                nouvelle_liste.append(item)
        return nouvelle_liste
    def select_caroussel_vols(self,liste,caroussel):
        """
        # recuperer les vols affectés à ce caroussel
        """
        nouvelle_liste = []
        for item in liste:
            if item[1]  == caroussel :
                nouvelle_liste.append(item[0])
        return nouvelle_liste
 

#---------------------------------------------------------------------------
"""
1. Distribution Uniforme (Approche Simpliste)
Hypothèse : Les passagers arrivent de manière équiprobable dans la plage horaire autorisée (entre 2h et 30 min avant le vol).
Modèle :Pour chaque vol, les passagers sont distribués uniformément sur la plage de 1h30 (90 minutes).

"""
class Simulate_uniforme(Simulate):
    def __init__(self,params):
        super().__init__(params,"Distribution uniforme") 

    def distribution(self, departure_min, open_time, close_time, max_pax):
        all_arrivals = []
        duration = close_time - open_time
     
        if max_pax == 0:
            return all_arrivals
            
        # Calcul du pas entre chaque passager
        step = duration / (max_pax + 1)

        # Répartition équitable des passagers dans l'intervalle
        for i in range(1, max_pax + 1):
            arrival_time = open_time + i * step
            all_arrivals.append(arrival_time)            
        return all_arrivals
#---------------------------------------------------------------------------
"""
 Distribution Normale (Gaussienne)
Hypothèse : Les passagers tendent à arriver autour d'un temps moyen (par exemple 1h15 avant le vol), avec une dispersion symétrique.
Modèle :
La distribution est centrée autour de 75 minutes avant le vol (milieu de la plage).
L'écart-type (σ) contrôle l'étalement (par exemple σ = 20 minutes).

Les passagers arrivent autour de 1h15 avant le vol (milieu de la plage)
L'écart-type (sigma_minutes) contrôle la dispersion :
    σ faible = arrivées groupées autour du milieu
    σ élevé = arrivées plus étalées

Paramètres ajustables :
    sigma_minutes : Contrôle l'étalement des arrivées (20-30 min donne un profil réaliste)

"""
class Simulate_normale(Simulate):
    def __init__(self,params,sigma_minutes= 20):
        super().__init__(params,"Distribution normale") 
        self.sigma_minutes= sigma_minutes   # Écart-type de la distribution (en minutes)

    def distribution(self,departure_min,open_time,close_time,max_pax):
        mean_time = departure_min - (self.params.open_min+self.params.close_min )/2   # Milieu de la plage (1h15 avant)
        sigma_minutes = self.sigma_minutes         
        all_arrivals=[]
        for _ in range(max_pax):
            while True:
                # Générer un temps aléatoire selon une distribution normale
                arrival_time = np.random.normal(loc=mean_time, scale=sigma_minutes)
                # Vérifier qu'il est dans la plage autorisée
                if open_time <= arrival_time <= close_time:
                    break
            all_arrivals.append(arrival_time)
        return all_arrivals


#---------------------------------------------------------------------------
"""
1-Distribution Exponentielle :
Hypothèse : Les passagers arrivent de manière aléatoire mais avec un taux d'arrivée décroissant à mesure que l'heure du vol approche (peu de passagers arrivent à la dernière minute).
Modèle :Le temps d'arrivée suit une loi exponentielle de paramètre 

Le paramètre lambda_param contrôle la décroissance :
    λ élevé = arrivées très concentrées au début
    λ faible = arrivées plus étalées

2-Comportement Généré :
Beaucoup d'arrivées juste après l'ouverture (2h avant)
Décroissance exponentielle vers la fermeture (30min avant)
Simule bien les passagers "prévoyants" qui arrivent tôt

3-Paramètres Clés :
lambda_param=0.03 : Valeur par défaut (essayez 0.02 à 0.05)

"""
class Simulate_poisson(Simulate):
    def __init__(self,params,lambda_param=0.03):
        super().__init__(params,"Distribution poisson") 
        self.lambda_param=lambda_param #Paramètre de taux pour la distribution exponentielle

    def distribution(self,departure_min,open_time,close_time,max_pax):
        window_duration = close_time - open_time
        all_arrivals=[]
        for _ in range(max_pax):
            arrival_offset = np.random.exponential(scale=1/self.lambda_param)
            arrival_time = open_time + min(arrival_offset, window_duration)
            all_arrivals.append(arrival_time)
        return all_arrivals

#---------------------------------------------------------------------------
"""
1-Distribution Beta :
    α (alpha) contrôle la concentration en début de plage
    β (beta) contrôle la concentration en fin de plage

    Exemples de profils :
    α=2, β=2 : Pic centré (comme une Gaussienne)
    α=1, β=3 : Early-birds (pic au début)
    α=3, β=1 : Last-minute (pic à la fin)
2-Avantages :
    Modélisation flexible des comportements
    Bornée naturellement entre 0 et 1 (redimensionnée à notre plage)
    Pas besoin de troncature artificielle

Paramètres Recommandés :
    Pour un aéroport d'affaires : α=1.5, β=2 (plus d'early-birds)
    Pour un aéroport de vacances : α=2, β=1.5 (plus étalé)
    Pour des retardataires : α=3, β=1
"""
class Simulate_beta(Simulate):
    def __init__(self,params,alpha=1,beta=3):
        super().__init__(params,"Distribution beta") 
        self.alpha=alpha  #Paramètre alpha de la distribution Beta (contrôle la forme gauche)
        self.beta=beta   #Paramètre beta de la distribution Beta (contrôle la forme droite)

    def distribution(self,departure_min,open_time,close_time,max_pax):
        window_duration = close_time - open_time
        beta_samples = np.random.beta(self.alpha, self.beta, size=max_pax)
        arrival_times = open_time + beta_samples * window_duration
        return arrival_times


#---------------------------------------------------------------------------
"""
Modèle Bimodal :
    Combine deux populations distinctes :
    -Early-birds (60-80% des passagers) : Arrivent autour de 1h-1h30 avant
    -Last-minute (20-40%) : Arrivent autour de 30-45min avant

Paramètres Clés :
    early_mean/late_mean : Position des pics (en minutes avant le vol)
    early_std/late_std : Dispersion des arrivées
    early_weight : Proportion de passagers early (0.6 = 60%)

Avantages :
    Capture mieux la réalité que les modèles unimodaux
    Permet d'ajuster finement les deux pics observés dans les aéroports
"""
class Simulate_bimodal(Simulate):
    def __init__(self,params,early_mean=90,early_std=20,late_mean=45,late_std=15,early_weight=0.7):
        super().__init__(params,"Distribution bimodal") 
        self.early_mean=early_mean     # Moyenne pour les early-birds (minutes avant le vol)
        self.early_std=early_std       # Écart-type pour les early-birds
        self.late_mean=late_mean       # Moyenne pour les last-minute (minutes avant le vol)
        self.late_std=late_std         # Écart-type pour les last-minute
        self.early_weight=early_weight # Proportion de passagers early-birds (0-1) 70% early, 30% late

    def distribution(self,departure_min,open_time,close_time,max_pax):
    
        # Générer les temps d'arrivée (mélange de deux distributions normales)
        n_early = int(max_pax * self.early_weight)
        n_late = max_pax - n_early
    
        # Early birds (pic vers 1h30 avant)
        early_arrivals = np.random.normal(loc=departure_min - self.early_mean, 
                                    scale=self.early_std, 
                                    size=n_early)
    
        # Last-minute (pic vers 45min avant)
        late_arrivals = np.random.normal(loc=departure_min - self.late_mean, 
                                    scale=self.late_std, 
                                    size=n_late)
        all_arrivals = np.concatenate([early_arrivals, late_arrivals])
        all_arrivals = np.clip(all_arrivals, open_time, close_time)
        return all_arrivals

#------------------------------------------------------------------------------------------------- 
"""
Distribution Log-normale
Description :
	Cette distribution est utile pour modéliser des phénomènes où les valeurs sont positives et asymétriques, comme les temps d'arrivée des passagers (beaucoup arrivent tôt, quelques-uns arrivent très tôt ou tard).
Paramètres :
	mu : moyenne du logarithme des temps.
	sigma : écart-type du logarithme des temps.
"""
class Simulate_lognormale(Simulate):
    def __init__(self, params, mu=4.0, sigma=0.5):
        super().__init__(params, "Distribution log-normale")
        self.mu = mu
        self.sigma = sigma

    def distribution(self, departure_min, open_time, close_time, max_pax):
        window_duration = close_time - open_time
        log_samples = np.random.lognormal(mean=self.mu, sigma=self.sigma, size=max_pax)
        # Normaliser pour ajuster à la plage horaire
        log_samples = (log_samples - np.min(log_samples)) / (np.max(log_samples) - np.min(log_samples))
        arrival_times = open_time + log_samples * window_duration
        return arrival_times
#------------------------------------------------------------------------------------------------- 
"""
Distribution Gamma
	Idéale pour modéliser des temps d'attente ou des arrivées avec une queue longue (peu de passagers arrivent très tard).
Paramètres :
	shape (k) : contrôle la forme de la distribution.
	scale (θ) : contrôle l'échelle.
"""
class Simulate_gamma(Simulate):
    def __init__(self, params, shape=2.0, scale=30.0):
        super().__init__(params, "Distribution Gamma")
        self.shape = shape
        self.scale = scale

    def distribution(self, departure_min, open_time, close_time, max_pax):
        window_duration = close_time - open_time
        if max_pax==0:
            return []
        gamma_samples = np.random.gamma(shape=self.shape, scale=self.scale, size=max_pax)
        # Normaliser pour ajuster à la plage horaire
        gamma_samples = (gamma_samples - np.min(gamma_samples)) / (np.max(gamma_samples) - np.min(gamma_samples))
        arrival_times = open_time + gamma_samples * window_duration
        return arrival_times
#------------------------------------------------------------------------------------------------- 
"""
Distribution de Weibull
	Flexible pour modéliser des comportements variés (early-birds ou last-minute) selon le paramètre de forme.
Paramètres :
	shape (k) : détermine si les arrivées sont précoces (k < 1) ou tardives (k > 1).
	scale (λ) : étire la distribution.
"""
class Simulate_weibull(Simulate):
    def __init__(self, params, shape=1.5, scale=60.0):
        super().__init__(params, "Distribution Weibull")
        self.shape = shape
        self.scale = scale

    def distribution(self, departure_min, open_time, close_time, max_pax):
        window_duration = close_time - open_time
        weibull_samples = np.random.weibull(a=self.shape, size=max_pax) * self.scale
        # Normaliser pour ajuster à la plage horaire
        weibull_samples = (weibull_samples - np.min(weibull_samples)) / (np.max(weibull_samples) - np.min(weibull_samples))
        arrival_times = open_time + weibull_samples * window_duration
        return arrival_times
#------------------------------------------------------------------------------------------------- 
"""
Distribution Tri-modale
	Extension de la distribution bimodale pour capturer trois pics distincts (exemple : early-birds, milieu, last-minute).
Paramètres :
	means : liste des moyennes des trois pics (ex : [150, 120, 90] minutes avant le vol).
	stds : écarts-types pour chaque pic.
	weights : proportions de passagers pour chaque pic (ex : [0.5, 0.3, 0.2]).
"""
class Simulate_trimodal(Simulate):
    def __init__(self, params, means=[150, 120, 90], stds=[20, 15, 10], weights=[0.5, 0.3, 0.2]):
        super().__init__(params, "Distribution Tri-modale")
        self.means = means
        self.stds = stds
        self.weights = weights

    def distribution(self, departure_min, open_time, close_time, max_pax):
        n_per_mode = [int(max_pax * w) for w in self.weights]
        n_per_mode[-1] = max_pax - sum(n_per_mode[:-1])  
        
        arrivals = []
        for mean, std, n in zip(self.means, self.stds, n_per_mode):
            arrivals.extend(np.random.normal(loc=departure_min - mean, scale=std, size=n))
        
        arrivals = np.clip(arrivals, open_time, close_time)
        return arrivals
#------------------------------------------------------------------------------------------------- 
"""
Distribution Pareto (pour modéliser les extrêmes)
Description :
	Utile pour simuler une minorité de passagers arrivant très tôt ou très tard (queue lourde).
Paramètres :
	alpha : paramètre de forme (ex : 2.0).
	scale : paramètre d'échelle.
"""
class Simulate_pareto(Simulate):
    def __init__(self, params, alpha=2.0, scale=30.0):
        super().__init__(params, "Distribution Pareto")
        self.alpha = alpha
        self.scale = scale

    def distribution(self, departure_min, open_time, close_time, max_pax):
        pareto_samples = (np.random.pareto(a=self.alpha, size=max_pax) + 1) * self.scale
        arrival_times = departure_min - pareto_samples
        arrival_times = np.clip(arrival_times, open_time, close_time)
        return arrival_times
#------------------------------------------------------------------------------------------------- 
"""
Distribution Binomiale Négative
Description :
    Modèle idéal pour les comptages avec surdispersion (variance > moyenne).
    Paramétrée via :
    - n : nombre de succès (lié à la dispersion)
    - p : probabilité de succès
    Alternative : paramétrisation par mu (moyenne) et k (dispersion)
Comportement :
    Pic plus large qu'une Poisson, queue plus épaisse.
    Capture mieux les fluctuations réelles dans les aéroports.
Paramètres Recommandés :
    Pour les voyageurs : mu=8, k=4 (basé sur vos données)
"""
class Simulate_binomialnegatif(Simulate):
    def __init__(self, params, mu=8, k=4):
        super().__init__(params, "Distribution Binomiale Négative")
        self.mu = mu  # Moyenne de la distribution
        self.k = k    # Paramètre de dispersion (plus k est petit, plus la dispersion est grande)
        
        # Conversion mu/k vers les paramètres n/p de la Binomiale Négative
        self.p = k / (k + mu)  # Probabilité de succès
        self.n = k             # Nombre de succès
    def distribution(self, departure_min, open_time, close_time, max_pax):
        window_duration = close_time - open_time
        if max_pax == 0:
            return []
        
        # Générer les temps d'arrivée par tranches de 10 minutes
        time_slots = np.arange(open_time, close_time, 10)
        n_slots = len(time_slots)
        
        # Générer les proportions par tranche avec Binomiale Négative
        arrivals_per_slot = np.random.negative_binomial(n=self.n, p=self.p, size=n_slots)
        
        # Normaliser et ajuster pour obtenir exactement max_pax arrivées
        arrivals_per_slot = (arrivals_per_slot / np.sum(arrivals_per_slot) * max_pax).astype(int)
        remaining = max_pax - np.sum(arrivals_per_slot)
        
        # Distribuer les restants dans les tranches aléatoirement
        if remaining > 0:
            indices = np.random.choice(n_slots, remaining, replace=True)
            np.add.at(arrivals_per_slot, indices, 1)
        
        # Générer les temps exacts
        all_arrivals = []
        for slot_idx, count in enumerate(arrivals_per_slot):
            if count == 0:
                continue
            slot_start = time_slots[slot_idx]
            arrivals_in_slot = np.random.uniform(slot_start, slot_start + 10, size=count)
            all_arrivals.extend(arrivals_in_slot)
        
        # Vérification finale (optionnelle)
        assert len(all_arrivals) == max_pax, f"Erreur: {len(all_arrivals)} arrivées au lieu de {max_pax}"
        
        return np.array(all_arrivals)
 #---------------------------------------------------------------------------



if __name__ == "__main__":
    params=Params()
    params.traitement=2
    params.date_str="2025-04-12"
    #params.compagnie="GROUPE AIR FRANCE"
    #params.num_vol="AF1777"
    sim=Simulate_uniforme(params=params)
    data=sim.run()

    
