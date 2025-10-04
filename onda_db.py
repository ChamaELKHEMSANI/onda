
import sqlite3
from datetime import datetime
import csv
import random



class Flight:
    def __init__(self,
                site,
                direction,
                flight_number,
                company,
                aircraft_type,
                scheduled_datetime,
                passenger_count
            ):
        self.site=site
        self.direction=direction
        self.flight_number=flight_number
        self.company=company
        self.aircraft_type=aircraft_type
        self.scheduled_datetime=scheduled_datetime
        self.passenger_count=passenger_count

        
    def __repr__(self):
        params_list = []
        for attr, value in vars(self).items():
            params_list.append(f"{attr}={value}")
        return "Flight(" + ", ".join(params_list) + ")"

class DBaircraft:
    def __init__(self,db_path):
        self.db_path = db_path

    def get_flights(self, site, date_str, compagnies=None, num_vols=None):
        """
        Récupère tous les vols pour une date donnée en fonction du champ DateHeurePrevue.
        Accepte maintenant des listes pour compagnies et num_vols.
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        params = [site, date_str, 'D', 'C']
        
        # Requête de base
        query = """
        SELECT Site, Sens, NumVol, Compagnie, TypeAvion, DateHeurePrevue, PAXpayants FROM aircraft     
        WHERE Site=? AND date(DateHeurePrevue) = ? AND Sens=? AND CarVol=?
        """
        
        # Gestion des compagnies (peut être une liste ou None)
        if compagnies:
            if isinstance(compagnies, str):
                compagnies = [compagnies]  # Convertit une string en liste à un élément
            placeholders = ','.join(['?'] * len(compagnies))
            query += f" AND Compagnie IN ({placeholders})"
            params.extend(compagnies)
        
        # Gestion des numéros de vol (peut être une liste ou None)
        if num_vols:
            if isinstance(num_vols, str):
                num_vols = [num_vols]  # Convertit une string en liste à un élément
            placeholders = ','.join(['?'] * len(num_vols))
            query += f" AND NumVol IN ({placeholders})"
            params.extend(num_vols)
        
        query += " ORDER BY DateHeurePrevue"
        
        cursor.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        flights = []
        for row in rows:
            flight = Flight(
                site=row['Site'],
                direction=row['Sens'],
                flight_number=row['NumVol'],
                company=row['Compagnie'],
                aircraft_type=row['TypeAvion'],
                scheduled_datetime=datetime.strptime(row['DateHeurePrevue'], '%Y-%m-%d %H:%M') if row['DateHeurePrevue'] else None,
                passenger_count=int(row['PAXpayants']),
            )
            flights.append(flight)
        
        conn.close()
        return flights

    def get_sites(self):
        """
        Récupère tous les sites 
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        

        query = """
        SELECT distinct Site FROM aircraft 
        ORDER BY Site
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        sites = []
        for row in rows:
            sites.append(row['Site'])
        
        conn.close()
        return sites

    def get_compagnies(self,site,date_str):
        """
        Récupère toutes les compagnies 
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        

        query = """
        SELECT distinct Compagnie FROM aircraft 
        WHERE Site=? AND date(DateHeurePrevue) = ? AND Sens=?  AND CarVol=? 
        ORDER BY Compagnie
        """
        
        cursor.execute(query, (site,date_str,'D','C'))
        rows = cursor.fetchall()
        
        compagnies = []
        for row in rows:
            compagnies.append(row['Compagnie'])
        
        conn.close()
        return compagnies

    def get_compagnies_period(self, site, start_date, end_date):
        """Retourne les compagnies ayant des vols entre les deux dates"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        
        query = """
            SELECT DISTINCT Compagnie 
            FROM aircraft 
            WHERE site = ?  AND Sens=?  AND CarVol=? 
            AND DateHeurePrevue BETWEEN ? AND ? 
            ORDER BY Compagnie
        """
        cursor.execute(query, (site,'D','C',start_date,end_date))
        rows = cursor.fetchall()
        
        compagnies = []
        for row in rows:
            compagnies.append(row['Compagnie'])
        
        conn.close()
        return compagnies




    def get_vols(self,site,date_str,compagnie):
        """
        Récupère toutes les compagnies 
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        

        query = """
        SELECT DISTINCT NumVol FROM aircraft 
        WHERE Site=? AND date(DateHeurePrevue) = ? AND Compagnie=? AND Sens=?  AND CarVol=?
        """
        
        cursor.execute(query, (site,date_str,compagnie,'D','C'))
        rows = cursor.fetchall()
        
        vols = []
        for row in rows:
            vols.append(row['NumVol'])
        
        conn.close()
        return vols

    def get_vols_period(self, site, start_date, end_date, compagnie):
        """Retourne les vols d'une compagnie entre les deux dates"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        

        query = """
            SELECT distinct NumVol 
            FROM aircraft 
            WHERE site = ?  AND Compagnie = ?  AND Sens=?  AND CarVol=?
            AND DateHeurePrevue BETWEEN ? AND ?
        """
        cursor.execute(query, (site,compagnie,'D','C',start_date,end_date))
        rows = cursor.fetchall()
        
        vols = []
        for row in rows:
            vols.append(row['NumVol'])
        
        conn.close()
        return vols

    def get_compagnies_info(self):
        """
        Récupère toutes les compagnies 
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        
        query = """
        SELECT compagnies,zone,caroussel FROM compagnies
        ORDER BY compagnies
        """
        
        cursor.execute(query)
        rows = cursor.fetchall()
        
        compagnies = {}
        for row in rows:
            compagnies[row['compagnies']]=row['caroussel']
        
        conn.close()
        return compagnies
    def get_All_compagnies(self,site):
        """
        Récupère toutes les compagnies 
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        

        query = """
        SELECT distinct Compagnie FROM aircraft 
        WHERE Site=?  AND Sens=?  AND CarVol=? 
        ORDER BY Compagnie
        """
        
        cursor.execute(query, (site,'D','C'))
        rows = cursor.fetchall()
        
        compagnies = []
        for row in rows:
            compagnies.append(row['Compagnie'])
        
        conn.close()
        return compagnies

    def get_All_flights(self,site):
        """
        Récupère toutes les flights 
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom
        cursor = conn.cursor()
        

        query = """
        SELECT distinct a.NumVol,c.compagnies,c.zone,c.caroussel FROM aircraft a,compagnies c
        WHERE a.Compagnie=c.compagnies AND Site=?  AND Sens=?  AND CarVol=?

        ORDER BY NumVol
        """
        
        cursor.execute(query, (site,'D','C'))
        rows = cursor.fetchall()
        
        flights = []
        for row in rows:
            flights.append([row['NumVol'],row['compagnies'],row['zone'],row['caroussel']])
        
        conn.close()
        return flights

    def get_compagnies_all(self):
        """Récupère toutes les compagnies avec leur zone et carrousel"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT compagnies, zone, caroussel FROM compagnies ORDER BY compagnies")
            return cursor.fetchall()

    def update_compagnies(self, compagnies):
        """Met à jour la table des compagnies avec les nouvelles données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Supprimer toutes les entrées existantes
            cursor.execute("DELETE FROM compagnies")
            
            # Insérer les nouvelles données
            cursor.executemany(
                "INSERT INTO compagnies (compagnies, zone, caroussel) VALUES (?, ?, ?)",
                compagnies
            )
            
            conn.commit()
if __name__ == "__main__":
    db=DBaircraft("onda_aircraft.db")
    """
    data=db.get_All_compagnies("GMMX")
    filename="compagnies_C.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['compagnies', 
                        'zone',
                        'caroussel'
                        ])
        for i in range(len(data)):
            zone='B'if(random.randint(1, 2)==2) else 'A'
            writer.writerow([
                            data[i],
                            zone,
                            random.randint(3,  5) if (zone=='B') else random.randint(1, 2)
                            ])
    """
    data=db.get_All_flights("GMMX")
 
    filename="flights.csv"
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['flight', 
                        'zone',
                        'caroussel'
                        ])
        for i in range(len(data)):

            writer.writerow([
                            data[i][0],
                            data[i][2],
                            data[i][3]
                            ])

    """
    data=db.get_flights( "GMMX", "2025-04-04")
    print(data)
    for i in range(len(data)):
        print(data[i])
    """
    