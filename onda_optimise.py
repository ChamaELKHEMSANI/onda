import random
import time
import math

from copy import deepcopy
from PyQt5.QtCore import QObject, pyqtSignal
from onda_db import DBaircraft
from onda_config import Params
from onda_simulation import Simulate
#------------------------------------------------------------------------------------------------- 
class OptimiseurGP(QObject): 
    progress_updated = pyqtSignal(int, str) 
    def __init__(self, simulation: Simulate,max_carrousel=5,optim_compagnies=True, population_size=20, generations=50, mutation_rate=0.1,elite_size=5):
        """
        Initialise l'algo génétique.
        """
        super().__init__() 
        self.simulation = simulation
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self.max_carrousel=max_carrousel
        self.optim_compagnies=optim_compagnies
        self.elite_size=elite_size
        self.current_generation=0
        if self.optim_compagnies:
            self.simulate_list = list(simulation.compagnies.keys())
            self.original_liste = deepcopy(self.simulation.compagnies)
        else:
            self.simulate_list = list(simulation.flights_carrousel.keys())
            self.original_liste = deepcopy(self.simulation.flights_carrousel)
            
 

        
    def create_individual(self):
        """Crée un individu (affectation aléatoire des compagnies aux carrousels)"""
        return {comp: random.randint(1, self.max_carrousel) for comp in self.simulate_list}
    
    def initialize_population(self) :
        """Initialise la population"""
        population= [self.create_individual() for _ in range(self.population_size-1)]
        population.append(deepcopy(self.original_liste))
        return population
    
    def evaluate(self, individual) :
        """Évalue un individu en lançant la simulation avec son affectation"""
 
        if self.optim_compagnies:
            self.simulation.init_db_compagnies( individual)
        else:
            self.simulation.init_db_flights( individual)
        
        data = self.simulation.run()
        result = self.simulation.simulate(data)
        random.seed(time.time())
        return result["nombre_echec"]
    
    def rank_population(self, population) :
        """Classe la population par fitness (nombre d'échecs)"""
        ranked = [(ind, self.evaluate(ind),0) for ind in population]
        return sorted(ranked, key=lambda x: x[1])
    
    def crossover_uniform(self, parent1, parent2):
        """Croisement uniforme"""
        child = {}
        for comp in self.simulate_list:
            if random.random() < 0.5:
                child[comp] = parent1[comp]
            else:
                child[comp] = parent2[comp]
        return child

    def crossover_cut(self, parent1, parent2,cut):
        items1 = list(parent1.items())
        items2 = list(parent2.items())
        items1=sorted(items1, key=lambda x: x[0])
        items2=sorted(items2, key=lambda x: x[0])
        coupure = len(items1)//cut
        child = dict(items1[:coupure]+items2[coupure:])
        return child

    def crossover_multicut(self, parent1, parent2,cut):
        items1 = list(parent1.items())
        items2 = list(parent2.items())
        items1=sorted(items1, key=lambda x: x[0])
        items2=sorted(items2, key=lambda x: x[0])
        nb_elem=len(items1)
        coupure = nb_elem//cut
        child = dict(items1[:coupure]+items2[coupure:nb_elem-coupure]+items1[coupure:])
        return child

    def crossover(self, parent1, parent2):

        mode = random.randint(1, 10)
        if  mode==1:
            return self.crossover_cut(parent1, parent2,2)
        elif  mode==2:
            return self.crossover_cut(parent2, parent1,2)
        elif  mode==3:
            return self.crossover_cut(parent1, parent2,3)
        elif  mode==4:
            return self.crossover_cut(parent2, parent1,3)
        elif  mode==5:
            return self.crossover_cut(parent1, parent2,4)
        elif  mode==6 :
            return self.crossover_cut(parent2, parent1,4)
        elif  mode==7:
            return self.crossover_multicut(parent1, parent2,3)
        elif  mode==8 :
            return self.crossover_multicut(parent2, parent1,3)
        else :
            return self.crossover_uniform(parent1, parent2)


    def mutate(self, individual) :
        """Mutation aléatoire"""
        key=random.choice(tuple(individual.keys()))
        individual[key] = random.randint(1, self.max_carrousel)
        print("mutate",key,individual[key])
        return individual

    def makeGeneration_random(self,ranked_population,generation):
        new_population =  ranked_population
        cpt=0
        while cpt < self.population_size :
            cpt+=1
            parent1, parent2 = random.sample(ranked_population, 2)
            child = self.crossover(parent1[0], parent2[0])
            if random.random() < self.mutation_rate:
                child = self.mutate(child)
            new_population.append((child, self.evaluate(child),generation))

        new_population=sorted(new_population, key=lambda x: x[1])
        new_population = new_population[:self.population_size]
        return new_population

    def makeGeneration_best_best(self,ranked_population,generation):
        new_population =  ranked_population
        cpt=0
        while cpt < self.population_size-1 :
            parent1, parent2 = ranked_population[cpt], ranked_population[cpt+1]
            child = self.crossover(parent1[0], parent2[0])
            if random.random() < self.mutation_rate:
                child = self.mutate(child)
            new_population.append((child, self.evaluate(child),generation))
            cpt+=1

        new_population=sorted(new_population, key=lambda x: x[1])
        new_population = new_population[:self.population_size]
        return new_population

    def makeGeneration_best_worst(self,ranked_population,generation):
        new_population =  ranked_population
        cpt=0
        while cpt < self.population_size/2 :
            parent1, parent2 = ranked_population[cpt], ranked_population[self.population_size-1-cpt]
            child = self.crossover(parent1[0], parent2[0])
            if random.random() < self.mutation_rate:
                child = self.mutate(child)
            new_population.append((child, self.evaluate(child),generation))
            cpt+=1

        new_population=sorted(new_population, key=lambda x: x[1])
        new_population = new_population[:self.population_size]
        return new_population

    def run(self) :
        """Exécute l'algorithme génétique"""
        self.progress_updated.emit(0, "initialisation de la population")
        population = self.initialize_population()
        self.progress_updated.emit(0, "calcule de la fitenesse de la population")
        ranked_population = self.rank_population(population)
        self.progress_updated.emit(0, "démarrage du traitement ")
        cpt=0
        for generation in range(self.generations):
            self.current_generation=generation

            cpt+=1
            if cpt % 3 == 0:
                print("makeGeneration_random")
                ranked_population=self.makeGeneration_random(ranked_population,generation)
            elif cpt % 3 == 1:
                print("makeGeneration_best_best")
                ranked_population=self.makeGeneration_best_best(ranked_population,generation)
            else:
                print("makeGeneration_best_worst")
                ranked_population=self.makeGeneration_best_worst(ranked_population,generation)

            print(generation,":",[(x[1],x[2]) for x in ranked_population])
            # Calcul du pourcentage de progression
            progress = int((generation / self.generations) * 100)
            best_score = ranked_population[0][1]
            self.progress_updated.emit(progress, f"Génération {generation}: Meilleur score = {best_score}")
            
            if(best_score==0):
                break
        self.progress_updated.emit(100, "Optimisation terminée")

        # Retourne le meilleur individu trouvé
        return ranked_population[0][0],ranked_population[0][1],self.original_liste
#---------------------------------------------------------------------------
