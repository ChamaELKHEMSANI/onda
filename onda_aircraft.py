import sys
import csv
import logging
import warnings
import os
import math
import random
from copy import deepcopy

warnings.filterwarnings("ignore")
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QProgressBar,QTextEdit,QListWidget,
                            QVBoxLayout, QHBoxLayout, QLabel,
                            QPushButton, QComboBox, QSlider, QSpinBox,
                            QSizePolicy,  QScrollArea, QSplitter,
                            QDoubleSpinBox, QGroupBox, QDateTimeEdit, QFileDialog,
                            QGraphicsEllipseItem, QGraphicsRectItem, QGraphicsLineItem, QGraphicsSimpleTextItem,QGraphicsPathItem,
                            QMessageBox, QCheckBox,QGraphicsView, QGraphicsScene,QStyle,QGraphicsTextItem,QGraphicsItemGroup,
                            QStyledItemDelegate, QTableView,QFormLayout)
from PyQt5.QtCore import Qt, QDate, QTimer,QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QIcon,QPainter, QBrush,QPen,QColor, QFont,QPainterPath,QStandardItemModel, QStandardItem




import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from onda_db import DBaircraft
from onda_config import Params
from onda_optimise import  OptimiseurGP 
from onda_simulation import (Simulate_uniforme, Simulate_normale,
                       Simulate_poisson, Simulate_binomialnegatif,Simulate_beta, Simulate_bimodal,
                       Simulate_lognormale, Simulate_gamma, Simulate_weibull,
                       Simulate_trimodal, Simulate_pareto)


class SimulationApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulation de Flux de bagages Aéroportuaire")
        self.setGeometry(100, 100, 1200, 800)
       
        # Paramètres par défaut
        self.params = Params()
        self.db = DBaircraft(self.params.db_path)
       
        # Création de l'interface
        self.setup_icons()
        self.setup_styles()
        self.initUI()

    def setup_icons(self):
        self.icons = {
            'params': self.style().standardIcon(QStyle.SP_FileDialogDetailedView),
            'info': self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            'edit': self.style().standardIcon(QStyle.SP_MessageBoxInformation),
            'simulate': self.style().standardIcon(QStyle.SP_MediaPlay),
            'visualise': self.style().standardIcon(QStyle.SP_ComputerIcon),
            'optimise': self.style().standardIcon(QStyle.SP_BrowserReload),  
            'export': self.style().standardIcon(QStyle.SP_DialogSaveButton),
            'reset': self.style().standardIcon(QStyle.SP_FileIcon),
            'expand': self.style().standardIcon(QStyle.SP_ArrowDown),
            'collapse': self.style().standardIcon(QStyle.SP_ArrowUp),
            'play': self.style().standardIcon(QStyle.SP_MediaPlay),
            'pause': self.style().standardIcon(QStyle.SP_MediaPause),
            'stop': self.style().standardIcon(QStyle.SP_MediaStop),
            'exit': self.style().standardIcon(QStyle.SP_DialogCloseButton)
        }


    def setup_styles(self):
        """Configure quelques styles CSS de base"""
        self.setStyleSheet("""
                            QPushButton {
                                padding: 5px;
                                min-width: 80px;
                                min-height: 30px;  /* Hauteur minimale */
                                max-height: 30px;  /* Hauteur maximale (pour fixer la hauteur) */
                            }

                            QGroupBox {
                                margin-top: 5px;
                                border: 1px solid #ccc;
                                border-radius: 5px;
                                padding-top: 5px;
                            }
                            QGroupBox::title {
                                subcontrol-origin: margin;
                                left: 5px;
                            }
                            QLabel {
                                margin: 5px;
                            }
                        """)

    def initUI(self):
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
       
        # Création des boutons
        self.create_boutons(main_layout)

        # Création des paramètres
        self.create_params(main_layout)

        # Graphiques
        self.fig = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.fig)
        self.canvas.setVisible(False)
        main_layout.addWidget(self.canvas)

        # Configurer les connexions entre les signaux et slots
        self.setup_connections()  

        # Charger les compagnies initiales
        self.update_compagnies()  

    def create_boutons(self, main_layout):
        """Crée les boutons"""
        button_container = QWidget()
        button_container.setFixedHeight(60)   
    
        bouton_layout = QHBoxLayout(button_container)  
        bouton_layout.setContentsMargins(5, 5, 5, 5)   
        
        
        # Bouton pour afficher/cacher les paramètres
        info_button = QPushButton(self.icons['info'], "Informations")
        info_button.clicked.connect(lambda: self.show_info("globaux"))
        
        # Option 2: Fixer la hauteur des boutons individuellement (plus courant)
        info_button.setFixedHeight(30)  # Hauteur fixe de 40 pixels
        bouton_layout.addWidget(info_button)
        
        self.globaux_params_button = QPushButton(self.icons['expand'], "Paramètres")
        self.globaux_params_button.clicked.connect(lambda: self.toggle_params_globaux())
        self.globaux_params_button.setFixedHeight(30)
        bouton_layout.addWidget(self.globaux_params_button)
        
        self.simulate_button = QPushButton(self.icons['simulate'], "Lancer la simulation")
        self.simulate_button.clicked.connect(self.run_simulation)
        self.simulate_button.setFixedHeight(30)
        bouton_layout.addWidget(self.simulate_button)
        
        self.visualise_button = QPushButton(self.icons['visualise'], " Visualise la simulation")
        self.visualise_button.clicked.connect(lambda: self.visualise_simulation())
        self.visualise_button.setFixedHeight(30)
        bouton_layout.addWidget(self.visualise_button)
         
        self.export_button = QPushButton(self.icons['export'], " Exporter en CSV")
        self.export_button.clicked.connect(lambda: self.export_to_csv())
        self.export_button.setFixedHeight(30)
        bouton_layout.addWidget(self.export_button)
        
        self.globaux_reset_button = QPushButton(self.icons['reset'], " Réinitialiser les paramètres")
        self.globaux_reset_button.clicked.connect(lambda: self.reset_params("globaux"))
        self.globaux_reset_button.setFixedHeight(30)
        bouton_layout.addWidget(self.globaux_reset_button)
        
        self.globaux_exit_button = QPushButton(self.icons['exit'], " Quitter")
        self.globaux_exit_button.clicked.connect(lambda: sys.exit(0))
        self.globaux_exit_button.setFixedHeight(30)
        bouton_layout.addWidget(self.globaux_exit_button)

        # Logos
        logo_layout = QHBoxLayout()
        self.logo_1_label = QLabel()
        self.logo_1_label.setPixmap(QPixmap("logo_1.png"))
        self.logo_1_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(self.logo_1_label)
        self.logo_2_label = QLabel()
        self.logo_2_label.setPixmap(QPixmap("logo_2.png"))
        self.logo_2_label.setAlignment(Qt.AlignCenter)
        logo_layout.addWidget(self.logo_2_label)
        bouton_layout.addLayout(logo_layout)

        main_layout.addWidget(button_container, Qt.AlignTop)


    def create_params(self,main_layout):
        """Crée  les paramètres globaux"""
        # Paramétres globaux
        self.params_globaux_group = QGroupBox("Paramétres globaux")
 
        params_globaux_V_layout = QVBoxLayout()

        params_globaux_H_layout = QHBoxLayout()

        # AirCraft
        aircraft_group = QGroupBox("AirCraft")
        aircraft_layout = QHBoxLayout()

        aircraft1_layout = QVBoxLayout()
        # Date
        date_layout = QHBoxLayout()
        label_date = QLabel("Date:")
        label_date.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        date_layout.addWidget(label_date)
        self.date_edit = QDateTimeEdit()
        self.date_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setMinimumWidth(150)  
        date_layout.addWidget(self.date_edit)
        aircraft1_layout.addLayout(date_layout)

        #Site
        site_layout = QHBoxLayout()
        label_site = QLabel("Site:")
        label_site.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        site_layout.addWidget(label_site)
        self.site_combo = QComboBox()
        self.site_combo.setMinimumWidth(150)  
        sites = self.db.get_sites()
        self.site_combo.addItems(sites)
        self.site_combo.setCurrentText(self.params.site)
        site_layout.addWidget(self.site_combo)
        aircraft1_layout.addLayout(site_layout)
        aircraft_layout.addLayout(aircraft1_layout)

        # Compagnies
        compagnie_group = QGroupBox("Compagnies:")
        compagnie_layout = QHBoxLayout()
        self.compagnie_list = QListWidget()
        self.compagnie_list.setSelectionMode(QListWidget.MultiSelection)
        self.compagnie_list.setMinimumWidth(150)  
        #self.compagnie_combo.setSizeAdjustPolicy(QComboBox.AdjustToContents)  
        compagnie_layout.addWidget(self.compagnie_list)
        compagnie_group.setLayout(compagnie_layout)
        aircraft_layout.addWidget(compagnie_group)

        # num_vol
        num_vol_group = QGroupBox("Vols:")
        num_vol_layout =  QHBoxLayout()
        self.num_vol_list = QListWidget()
        self.num_vol_list.setSelectionMode(QListWidget.MultiSelection)
        self.num_vol_list.setMinimumWidth(150)  
        num_vol_layout.addWidget(self.num_vol_list)
        num_vol_group.setLayout(num_vol_layout)
        aircraft_layout.addWidget(num_vol_group)

        carrousel_group = QGroupBox("Carrousel")
        optimise_layout = QHBoxLayout()
        self.edit_compagnie_button = QPushButton(  " editer ")
        self.edit_compagnie_button.clicked.connect(lambda: self.edit_compagnie())
        self.edit_compagnie_button.setFixedHeight(10)
        optimise_layout.addWidget(self.edit_compagnie_button)
        carrousel_group.setLayout(optimise_layout)
        aircraft_layout.addWidget(carrousel_group)

        aircraft_group.setFixedHeight(170)
        aircraft_group.setLayout(aircraft_layout)
        params_globaux_V_layout.addWidget(aircraft_group)

 


        # Plage horaire
        time_group = QGroupBox("Plage horaire")
        time_layout = QVBoxLayout()
       
        # Heure de début
        start_layout = QHBoxLayout()
        start_layout.addWidget(QLabel("Début:"))
        self.start_hour = QSpinBox()
        self.start_hour.setRange(0, 23)
        self.start_hour.setValue(0)
        label_start_hour = QLabel("H:")
        label_start_hour.setAlignment(Qt.AlignRight)
        start_layout.addWidget(label_start_hour)
        start_layout.addWidget(self.start_hour)
        self.start_min = QSpinBox()
        self.start_min.setRange(0, 59)
        self.start_min.setValue(0)
        label_start_min = QLabel("M:")
        label_start_min.setAlignment(Qt.AlignRight)
        start_layout.addWidget(label_start_min)
        start_layout.addWidget(self.start_min)
        time_layout.addLayout(start_layout)
       
        # Heure de fin
        end_layout = QHBoxLayout()
        end_layout.addWidget(QLabel("Fin:"))
        self.end_hour = QSpinBox()
        self.end_hour.setRange(0, 23)
        self.end_hour.setValue(23)
        label_end_hour = QLabel("H:")
        label_end_hour.setAlignment(Qt.AlignRight)
        end_layout.addWidget(label_end_hour)
        end_layout.addWidget(self.end_hour)
        self.end_min = QSpinBox()
        self.end_min.setRange(0, 59)
        self.end_min.setValue(59)
        label_end_min = QLabel("M:")
        label_end_min.setAlignment(Qt.AlignRight)
        end_layout.addWidget(label_end_min)
        end_layout.addWidget(self.end_min)
        time_layout.addLayout(end_layout)
       
        # Pas de temps
        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Pas de temps:"))
        self.step_spin = QSpinBox()
        self.step_spin.setRange(1, 60)
        self.step_spin.setValue(self.params.step_time)
        label_step_min = QLabel("(min)")
        label_step_min.setAlignment(Qt.AlignRight)
        step_layout.addWidget(label_step_min)
        step_layout.addWidget(self.step_spin)
        time_layout.addLayout(step_layout)
       
        time_group.setFixedHeight(140)
        time_group.setLayout(time_layout)
        params_globaux_H_layout.addWidget(time_group)
       
        # Paramètres d'enregistrement
        checkin_group = QGroupBox("Enregistrement")
        checkin_layout = QVBoxLayout()
       
        # Ouverture avant le vol
        open_layout = QHBoxLayout()
        open_layout.addWidget(QLabel("Ouverture (min):"))
        self.open_spin = QSpinBox()
        self.open_spin.setRange(60, 240)
        self.open_spin.setValue(self.params.open_min)
        open_layout.addWidget(self.open_spin)
        checkin_layout.addLayout(open_layout)
       
        # Fermeture avant le vol
        close_layout = QHBoxLayout()
        close_layout.addWidget(QLabel("Fermeture (min):"))
        self.close_spin = QSpinBox()
        self.close_spin.setRange(15, 120)
        self.close_spin.setValue(self.params.close_min)
        close_layout.addWidget(self.close_spin)
        checkin_layout.addLayout(close_layout)
       
        checkin_group.setFixedHeight(100)
        checkin_group.setLayout(checkin_layout)
        params_globaux_H_layout.addWidget(checkin_group)

        # Paramètres Bagages
        Bagages_group = QGroupBox("Bagages")
        Bagages_layout = QVBoxLayout()

        # Nombre max de bagages
        baggage_layout = QHBoxLayout()
        baggage_layout.addWidget(QLabel("Nombre Max:"))
        self.baggage_spin = QSpinBox()
        self.baggage_spin.setRange(1, 10)
        self.baggage_spin.setValue(self.params.max_bagage)
        baggage_layout.addWidget(self.baggage_spin)
        Bagages_layout.addLayout(baggage_layout)

        # Poids moyen de bagages
        poids_moyen_baggage_layout = QHBoxLayout()
        poids_moyen_baggage_layout.addWidget(QLabel("Poids moyen:"))
        self.poids_moyen_baggage_spin = QSpinBox()
        self.poids_moyen_baggage_spin.setRange(1, 50)
        self.poids_moyen_baggage_spin.setValue(self.params.poids_moyen_bagage)
        poids_moyen_baggage_layout.addWidget(self.poids_moyen_baggage_spin)
        Bagages_layout.addLayout(poids_moyen_baggage_layout)

        # Poids moyen de bagages
        longueur_moyen_baggage_layout = QHBoxLayout()
        longueur_moyen_baggage_layout.addWidget(QLabel("Longueur moyenne:"))
        self.longueur_moyen_baggage_spin = QDoubleSpinBox()
        self.longueur_moyen_baggage_spin.setRange(0.5, 2.0)
        self.longueur_moyen_baggage_spin.setSingleStep(0.1)
        self.longueur_moyen_baggage_spin.setValue(self.params.longueur_moyenne_bagage)
        longueur_moyen_baggage_layout.addWidget(self.longueur_moyen_baggage_spin)
        Bagages_layout.addLayout(longueur_moyen_baggage_layout)
        Bagages_group.setFixedHeight(140)
        Bagages_group.setLayout(Bagages_layout)
        params_globaux_H_layout.addWidget(Bagages_group)


        # Paramètres Convoyeur
        Convoyeur_group = QGroupBox("Traitements")
        Convoyeur_layout = QVBoxLayout()

        # traitement_moyen_bagage
        traitement_moyen_layout = QHBoxLayout()
        traitement_moyen_layout.addWidget(QLabel("Traitement moyen(val/min):"))
        self.traitement_moyen_spin = QSpinBox()
        self.traitement_moyen_spin.setRange(1, 10)
        self.traitement_moyen_spin.setValue(self.params.traitement)
        traitement_moyen_layout.addWidget(self.traitement_moyen_spin)
        Convoyeur_layout.addLayout(traitement_moyen_layout)

        # poids_max_tapis
        poids_max_tapis_layout = QHBoxLayout()
        poids_max_tapis_layout.addWidget(QLabel("Poids max-Carrousel(kg):"))
        self.poids_max_tapis_spin = QSpinBox()
        self.poids_max_tapis_spin.setRange(1000, 10000)
        self.poids_max_tapis_spin.setValue(self.params.poids_max)
        poids_max_tapis_layout.addWidget(self.poids_max_tapis_spin)
        Convoyeur_layout.addLayout(poids_max_tapis_layout)

        # longueur_tapis
        longueur_tapis_layout = QHBoxLayout()
        longueur_tapis_layout.addWidget(QLabel("Longueur max-Carrousel(M):"))
        self.longueur_tapis_spin = QSpinBox()
        self.longueur_tapis_spin.setRange(10, 100)
        self.longueur_tapis_spin.setValue(self.params.longueur_max)
        longueur_tapis_layout.addWidget(self.longueur_tapis_spin)
        Convoyeur_layout.addLayout(longueur_tapis_layout)
        Convoyeur_group.setFixedHeight(140)
        Convoyeur_group.setLayout(Convoyeur_layout)
        params_globaux_H_layout.addWidget(Convoyeur_group)

        params_globaux_V_layout.addLayout(params_globaux_H_layout)

        # Cases à cocher pour choisir les graphes
        self.graphs_group = QGroupBox("Graphes à afficher")
        graphs_layout = QHBoxLayout()
       
        self.vols_check = QCheckBox("vols")
        self.vols_check.setChecked(False)
        graphs_layout.addWidget(self.vols_check)

        self.manutentionnaires_check = QCheckBox("Manutentionnaires")
        self.manutentionnaires_check.setChecked(False)
        graphs_layout.addWidget(self.manutentionnaires_check)

        self.enregistrements_check = QCheckBox("Enregistrements")
        self.enregistrements_check.setChecked(False)
        graphs_layout.addWidget(self.enregistrements_check)
       
        self.voyageurs_check = QCheckBox("Voyageurs")
        self.voyageurs_check.setChecked(False)
        graphs_layout.addWidget(self.voyageurs_check)
       
        self.bagages_check = QCheckBox("Bagages")
        self.bagages_check.setChecked(False)
        graphs_layout.addWidget(self.bagages_check)

        self.tapis_check1 = QCheckBox("Zone A Caroussel 1")
        self.tapis_check1.setChecked(False)
        graphs_layout.addWidget(self.tapis_check1)
        self.tapis_check2 = QCheckBox("Zone A Caroussel 2")
        self.tapis_check2.setChecked(False)
        graphs_layout.addWidget(self.tapis_check2)

        self.tapis_check3 = QCheckBox("Zone B Caroussel 1")
        self.tapis_check3.setChecked(False)
        graphs_layout.addWidget(self.tapis_check3)
        self.tapis_check4 = QCheckBox("Zone B Caroussel 2")
        self.tapis_check4.setChecked(False)
        graphs_layout.addWidget(self.tapis_check4)
        self.tapis_check5 = QCheckBox("Zone B Caroussel 3")
        self.tapis_check5.setChecked(False)
        graphs_layout.addWidget(self.tapis_check5)
       
        self.graphs_group.setFixedHeight(80)
        self.graphs_group.setLayout(graphs_layout)
        params_globaux_V_layout.addWidget(self.graphs_group)


        self.create_distributions(params_globaux_V_layout)

        self.params_globaux_group.setLayout(params_globaux_V_layout)
        main_layout.addWidget(self.params_globaux_group)


    def create_distributions(self,params_globaux_layout):
        # paramétre pour les différentes simulations

        self.params_distribution_group = QGroupBox("Distributions")
        params_distribution_layout = QVBoxLayout()

        # Contrôle de choix de la simulation
        simul_group = QGroupBox("Choix :")
        simul_layout = QHBoxLayout()

        choix_layout = QHBoxLayout()
        simul_label=QLabel("Loi de distribution:")
        simul_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        choix_layout.addWidget(simul_label)
        self.simul_combo = QComboBox()
        self.simul_combo.addItems(["uniform", "normal", "poisson","binomialnegatif", "beta","bimodal","trimodal","lognormal","gamma","weibull","pareto"])
        self.simul_combo.setCurrentText("uniform")
        choix_layout.addWidget(self.simul_combo)
        simul_layout.addLayout(choix_layout)


        info_button = QPushButton( "Information")
        info_button.clicked.connect(lambda: self.show_info(""))
        simul_layout.addWidget(info_button)

        reset_button = QPushButton( "Réinitialisation de paramètres")
        reset_button.clicked.connect(lambda: self.reset_params(""))
        simul_layout.addWidget(reset_button)

        variation_button = QPushButton( "Variation de paramètres")
        variation_button.clicked.connect(lambda: self.variation())
        simul_layout.addWidget(variation_button)

        simulation_periode_button = QPushButton( "Simulation sur une période")
        simulation_periode_button.clicked.connect(lambda: self.simulation_periode())
        simul_layout.addWidget(simulation_periode_button)

        self.optimise_compagnie_button = QPushButton(  "Optimisation par carrousel")
        self.optimise_compagnie_button.clicked.connect(lambda: self.optimise())
        self.optimise_compagnie_button.setFixedHeight(10)
        simul_layout.addWidget(self.optimise_compagnie_button)

        self.optimise_traitement_button = QPushButton(  "Optimisation par valeur de traitement")
        self.optimise_traitement_button.clicked.connect(lambda: self.optimise_traitement())
        self.optimise_traitement_button.setFixedHeight(10)
        simul_layout.addWidget(self.optimise_traitement_button)

        """
        self.optimise_duree_button = QPushButton(  "Optimisation par période d'enregistrement")
        self.optimise_duree_button.clicked.connect(lambda: self.optimise_duree())
        self.optimise_duree_button.setFixedHeight(10)
        simul_layout.addWidget(self.optimise_duree_button)
        """

        simul_group.setFixedHeight(80)
        simul_group.setLayout(simul_layout)
        params_distribution_layout.addWidget(simul_group)

        self.create_uniform_params(params_distribution_layout)
        self.create_normal_params(params_distribution_layout)
        self.create_poisson_params(params_distribution_layout)
        self.create_binomialnegatif_params(params_distribution_layout)
        self.create_beta_params(params_distribution_layout)
        self.create_bimodal_params(params_distribution_layout)
        self.create_trimodal_params(params_distribution_layout)  
        self.create_lognormal_params(params_distribution_layout)  
        self.create_gamma_params(params_distribution_layout)      
        self.create_weibull_params(params_distribution_layout)    
        self.create_pareto_params(params_distribution_layout)    

        self.uniform_params_group.setVisible(True)
       
        self.params_distribution_group.setLayout(params_distribution_layout)
        params_globaux_layout.addWidget(self.params_distribution_group)



    def create_uniform_params(self,distribution_layout):

        # Groupe de paramètres
        self.uniform_params_group = QGroupBox("Paramètres de la distribution uniforme")
        self.uniform_params_group.setVisible(False)
        param_layout = QVBoxLayout()
       
        info_label = QLabel("Cette distribution répartit uniformément les passagers entre l'ouverture et la fermeture.")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)

        self.uniform_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.uniform_params_group)
       


    def create_normal_params(self,distribution_layout):

        # Paramètres
        self.normal_params_group = QGroupBox("Paramètres de la distribution normale")
        self.normal_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        
        info_label = QLabel("Distribution centrée autour de 2h avant le vol avec dispersion contrôlée par l'écart-type.")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        
        sigma_layout = QHBoxLayout()
        sigma_label=QLabel("Écart-type (σ, en minutes):")
        sigma_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        sigma_layout.addWidget(sigma_label)
        self.sigma_spin = QDoubleSpinBox()
        self.sigma_spin.setRange(5, 60)
        self.sigma_spin.setValue(self.params.default_sigma)
        self.sigma_spin.setSingleStep(1)
        sigma_layout.addWidget(self.sigma_spin)
        param_layout.addLayout(sigma_layout)
 

        self.normal_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.normal_params_group)




    def create_poisson_params(self,distribution_layout):

        # Paramètres
        self.poisson_params_group = QGroupBox("Paramètres de la distribution poisson")
        self.poisson_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        
        info_label = QLabel("Distribution avec beaucoup d'arrivées au début puis décroissance exponentielle")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        
        lambda_layout = QHBoxLayout()
        lambda_label=QLabel("Paramètre lambda (λ):")
        lambda_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        lambda_layout.addWidget(lambda_label )
        self.lambda_spin = QDoubleSpinBox()
        self.lambda_spin.setRange(0.01, 0.1)
        self.lambda_spin.setValue(self.params.default_lambda)
        self.lambda_spin.setSingleStep(0.01)
        lambda_layout.addWidget(self.lambda_spin)
        param_layout.addLayout(lambda_layout)
 
        self.poisson_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.poisson_params_group)



    def create_beta_params(self,distribution_layout):

        # Paramètres
        self.beta_params_group = QGroupBox("Paramètres de la distribution Beta")
        self.beta_params_group.setVisible(False)
        param_layout = QVBoxLayout()
         
        info_label = QLabel("Distribution flexible contrôlée par alpha (concentration début) et beta (concentration fin)")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
         
       
        alpha_layout = QHBoxLayout()
        alpha_label=QLabel("Paramètre alpha (α):")
        alpha_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        alpha_layout.addWidget(alpha_label)
        self.alpha_spin = QDoubleSpinBox()
        self.alpha_spin.setRange(0.1, 5)
        self.alpha_spin.setValue(self.params.default_alpha)
        self.alpha_spin.setSingleStep(0.1)
        alpha_layout.addWidget(self.alpha_spin)
        param_layout.addLayout(alpha_layout)
       
        beta_layout = QHBoxLayout()
        beta_label=QLabel("Paramètre beta (β):")
        beta_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        beta_layout.addWidget(beta_label)
        self.beta_spin = QDoubleSpinBox()
        self.beta_spin.setRange(0.1, 5)
        self.beta_spin.setValue(self.params.default_beta)
        self.beta_spin.setSingleStep(0.1)
        beta_layout.addWidget(self.beta_spin)
        param_layout.addLayout(beta_layout)

       
        self.beta_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.beta_params_group)
       
    def create_binomialnegatif_params(self,distribution_layout):

        # Paramètres
        self.binomialnegatif_params_group = QGroupBox("Paramètres de la distribution Binomiale Négative")
        self.binomialnegatif_params_group.setVisible(False)
        param_layout = QVBoxLayout()
         
        info_label = QLabel("Distribution Binomiale Négative contrôlée par mu (Moyenne de la distribution) et k (Paramètre de dispersion)")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
         
       
        mu_layout = QHBoxLayout()
        mu_label=QLabel("Paramètre mu :")
        mu_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        mu_layout.addWidget(mu_label)
        self.mu_spin = QDoubleSpinBox()
        self.mu_spin.setRange(0.1, 10)
        self.mu_spin.setValue(self.params.default_mu)
        self.mu_spin.setSingleStep(0.1)
        mu_layout.addWidget(self.mu_spin)
        param_layout.addLayout(mu_layout)
       
        k_layout = QHBoxLayout()
        k_label=QLabel("Paramètre k :")
        k_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        k_layout.addWidget(k_label)
        self.k_spin = QDoubleSpinBox()
        self.k_spin.setRange(0.1, 10)
        self.k_spin.setValue(self.params.default_k)
        self.k_spin.setSingleStep(0.1)
        k_layout.addWidget(self.k_spin)
        param_layout.addLayout(k_layout)

       
        self.binomialnegatif_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.binomialnegatif_params_group)
       

    def create_bimodal_params(self,distribution_layout):
 
        # Paramètres
        self.bimodal_params_group  = QGroupBox("Paramètres de la distribution bimodale")
        self.bimodal_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        """
        info_label = QLabel("Combine deux populations: early-birds (arrivent tôt) et last-minute (arrivent juste avant)")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        """
        early_mean_layout = QHBoxLayout()
        early_mean_label=QLabel("Moyenne early (min):")
        early_mean_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        early_mean_layout.addWidget(early_mean_label)
        self.early_mean_spin = QSpinBox()
        self.early_mean_spin.setRange(60, 180)
        self.early_mean_spin.setValue(self.params.default_early_mean)
        early_mean_layout.addWidget(self.early_mean_spin)
        param_layout.addLayout(early_mean_layout)
       
        early_std_layout = QHBoxLayout()
        early_std_label=QLabel("Écart-type early:")
        early_std_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        early_std_layout.addWidget(early_std_label)
        self.early_std_spin = QSpinBox()
        self.early_std_spin.setRange(5, 60)
        self.early_std_spin.setValue(int(self.params.default_early_std))
        early_std_layout.addWidget(self.early_std_spin)
        param_layout.addLayout(early_std_layout)
       
        late_mean_layout = QHBoxLayout()
        late_mean_label=QLabel("Moyenne late (min):")
        late_mean_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        late_mean_layout.addWidget(late_mean_label)
        self.late_mean_spin = QSpinBox()
        self.late_mean_spin.setRange(15, 60)
        self.late_mean_spin.setValue(self.params.default_late_mean)
        late_mean_layout.addWidget(self.late_mean_spin)
        param_layout.addLayout(late_mean_layout)
       
        late_std_layout = QHBoxLayout()
        late_std_label=QLabel("Écart-type late:")
        late_std_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        late_std_layout.addWidget(late_std_label)
        self.late_std_spin = QSpinBox()
        self.late_std_spin.setRange(5, 30)
        self.late_std_spin.setValue(self.params.default_late_std)
        late_std_layout.addWidget(self.late_std_spin)
        param_layout.addLayout(late_std_layout)
       
        early_weight_layout = QHBoxLayout()
        early_weight_label=QLabel("Poids early:")
        early_weight_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        early_weight_layout.addWidget(early_weight_label)
        self.early_weight_slider = QSlider(Qt.Horizontal)
        self.early_weight_slider.setRange(10, 90)
        self.early_weight_slider.setValue(int(100*self.params.default_early_weight))
        early_weight_layout.addWidget(self.early_weight_slider)
        self.early_weight_label = QLabel(str(self.params.default_early_weight))
        early_weight_layout.addWidget(self.early_weight_label)
        param_layout.addLayout(early_weight_layout)
       
        self.early_weight_slider.valueChanged.connect(
            lambda: self.early_weight_label.setText(f"{self.early_weight_slider.value()/100:.2f}")
        )


       
        self.bimodal_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.bimodal_params_group)



    def create_lognormal_params(self,distribution_layout):
        # Paramètres
        self.lognormal_params_group = QGroupBox("Paramètres de la distribution log-normale")
        self.lognormal_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        
        info_label = QLabel("Distribution asymétrique utile pour modéliser des phénomènes où les valeurs sont positives et asymétriques")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        
        mu_layout = QHBoxLayout()
        lognormal_mu_label=QLabel("Paramètre mu (μ):")
        lognormal_mu_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        mu_layout.addWidget(lognormal_mu_label)
        self.lognormal_mu_spin = QDoubleSpinBox()
        self.lognormal_mu_spin.setRange(0.1, 10.0)
        self.lognormal_mu_spin.setValue(self.params.default_lognormal_mu)
        self.lognormal_mu_spin.setSingleStep(0.1)
        mu_layout.addWidget(self.lognormal_mu_spin)
        param_layout.addLayout(mu_layout)
       
        sigma_layout = QHBoxLayout()
        lognormal_sigma_label=QLabel("Paramètre sigma (σ):")
        lognormal_sigma_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        sigma_layout.addWidget(lognormal_sigma_label)
        self.lognormal_sigma_spin = QDoubleSpinBox()
        self.lognormal_sigma_spin.setRange(0.1, 2.0)
        self.lognormal_sigma_spin.setValue(self.params.default_lognormal_sigma)
        self.lognormal_sigma_spin.setSingleStep(0.1)
        sigma_layout.addWidget(self.lognormal_sigma_spin)
        param_layout.addLayout(sigma_layout)

        self.lognormal_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.lognormal_params_group)
       


    def create_gamma_params(self,distribution_layout):

        # Paramètres
        self.gamma_params_group = QGroupBox("Paramètres de la distribution Gamma")
        self.gamma_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        
        info_label = QLabel("Distribution idéale pour modéliser des temps d'attente avec une queue longue")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        
        shape_layout = QHBoxLayout()
        gamma_shape_label=QLabel("Paramètre shape (k):")
        gamma_shape_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        shape_layout.addWidget(gamma_shape_label)
        self.gamma_shape_spin = QDoubleSpinBox()
        self.gamma_shape_spin.setRange(0.1, 10.0)
        self.gamma_shape_spin.setValue(self.params.default_gamma_shape)
        self.gamma_shape_spin.setSingleStep(0.1)
        shape_layout.addWidget(self.gamma_shape_spin)
        param_layout.addLayout(shape_layout)
       
        scale_layout = QHBoxLayout()
        gamma_scale_label=QLabel("Paramètre scale (θ):")
        gamma_scale_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        scale_layout.addWidget(gamma_scale_label)
        self.gamma_scale_spin = QDoubleSpinBox()
        self.gamma_scale_spin.setRange(1.0, 100.0)
        self.gamma_scale_spin.setValue(self.params.default_gamma_scale)
        self.gamma_scale_spin.setSingleStep(1.0)
        scale_layout.addWidget(self.gamma_scale_spin)
        param_layout.addLayout(scale_layout)



        self.gamma_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.gamma_params_group)
       
 

    def create_weibull_params(self,distribution_layout):

        # Paramètres
        self.weibull_params_group = QGroupBox("Paramètres de la distribution Weibull")
        self.weibull_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        
        info_label = QLabel("Distribution flexible pour modéliser des comportements variés selon le paramètre de forme")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        
        shape_layout = QHBoxLayout()
        weibull_shape_label=QLabel("Paramètre shape (k):")
        weibull_shape_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        shape_layout.addWidget(weibull_shape_label)
        self.weibull_shape_spin = QDoubleSpinBox()
        self.weibull_shape_spin.setRange(0.1, 5.0)
        self.weibull_shape_spin.setValue(self.params.default_weibull_shape)
        self.weibull_shape_spin.setSingleStep(0.1)
        shape_layout.addWidget(self.weibull_shape_spin)
        param_layout.addLayout(shape_layout)
       
        scale_layout = QHBoxLayout()
        weibull_scale_label=QLabel("Paramètre scale (λ):")
        weibull_scale_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        scale_layout.addWidget(weibull_scale_label)
        self.weibull_scale_spin = QDoubleSpinBox()
        self.weibull_scale_spin.setRange(1.0, 100.0)
        self.weibull_scale_spin.setValue(self.params.default_weibull_scale)
        self.weibull_scale_spin.setSingleStep(1.0)
        scale_layout.addWidget(self.weibull_scale_spin)
        param_layout.addLayout(scale_layout)

        self.weibull_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.weibull_params_group)
       


    def create_trimodal_params(self,distribution_layout):


        # Paramètres
        self.trimodal_params_group = QGroupBox("Paramètres de la distribution Tri-modale")
        self.trimodal_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        """
        info_label = QLabel("Extension de la distribution bimodale pour capturer trois pics distincts")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(30)
        param_layout.addWidget(info_label)
        """
        # Moyennes
        means_group = QGroupBox("Moyennes (minutes avant le vol)")
        means_layout = QHBoxLayout()
       
        trimodal_mean1_label=QLabel("Pic 1:")
        trimodal_mean1_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        means_layout.addWidget(trimodal_mean1_label)
        self.trimodal_mean1_spin = QSpinBox()
        self.trimodal_mean1_spin.setRange(60, 240)
        self.trimodal_mean1_spin.setValue(self.params.default_trimodal_means[0])
        means_layout.addWidget(self.trimodal_mean1_spin)
       
        trimodal_mean2_label=QLabel("Pic 2:")
        trimodal_mean2_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        means_layout.addWidget(trimodal_mean2_label)
        self.trimodal_mean2_spin = QSpinBox()
        self.trimodal_mean2_spin.setRange(30, 180)
        self.trimodal_mean2_spin.setValue(self.params.default_trimodal_means[1])
        means_layout.addWidget(self.trimodal_mean2_spin)
       
        trimodal_mean3_label=QLabel("Pic 3:")
        trimodal_mean3_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        means_layout.addWidget(trimodal_mean3_label)
        self.trimodal_mean3_spin = QSpinBox()
        self.trimodal_mean3_spin.setRange(15, 120)
        self.trimodal_mean3_spin.setValue(self.params.default_trimodal_means[2])
        means_layout.addWidget(self.trimodal_mean3_spin)
       
        means_group.setFixedHeight(50)
        means_group.setLayout(means_layout)
        param_layout.addWidget(means_group)

        # Écarts-types
        stds_group = QGroupBox("Écarts-types")
        stds_layout = QHBoxLayout()
       
        trimodal_std1_label=QLabel("Pic 1:")
        trimodal_std1_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        stds_layout.addWidget(trimodal_std1_label)
        self.trimodal_std1_spin = QSpinBox()
        self.trimodal_std1_spin.setRange(5, 60)
        self.trimodal_std1_spin.setValue(self.params.default_trimodal_stds[0])
        stds_layout.addWidget(self.trimodal_std1_spin)
       
        trimodal_std2_label=QLabel("Pic 2:")
        trimodal_std2_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        stds_layout.addWidget(trimodal_std2_label)
        self.trimodal_std2_spin = QSpinBox()
        self.trimodal_std2_spin.setRange(5, 45)
        self.trimodal_std2_spin.setValue(self.params.default_trimodal_stds[1])
        stds_layout.addWidget(self.trimodal_std2_spin)
       
        trimodal_std3_label=QLabel("Pic 3:")
        trimodal_std3_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        stds_layout.addWidget(trimodal_std3_label)
        self.trimodal_std3_spin = QSpinBox()
        self.trimodal_std3_spin.setRange(5, 30)
        self.trimodal_std3_spin.setValue(self.params.default_trimodal_stds[2])
        stds_layout.addWidget(self.trimodal_std3_spin)
        stds_group.setFixedHeight(50)
        stds_group.setLayout(stds_layout)
        param_layout.addWidget(stds_group)

        # Poids
        weights_group = QGroupBox("Proportions (doivent sommer à 1)")
        weights_layout = QHBoxLayout()
       
        trimodal_weight1_label=QLabel("Pic 1:")
        trimodal_weight1_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        weights_layout.addWidget(trimodal_weight1_label)
        self.trimodal_weight1_spin = QDoubleSpinBox()
        self.trimodal_weight1_spin.setRange(0.0, 1.0)
        self.trimodal_weight1_spin.setValue(self.params.default_trimodal_weights[0])
        self.trimodal_weight1_spin.setSingleStep(0.05)
        weights_layout.addWidget(self.trimodal_weight1_spin)
       
        trimodal_weight2_label=QLabel("Pic 2:")
        trimodal_weight2_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        weights_layout.addWidget(trimodal_weight2_label)
        self.trimodal_weight2_spin = QDoubleSpinBox()
        self.trimodal_weight2_spin.setRange(0.0, 1.0)
        self.trimodal_weight2_spin.setValue(self.params.default_trimodal_weights[1])
        self.trimodal_weight2_spin.setSingleStep(0.05)
        weights_layout.addWidget(self.trimodal_weight2_spin)
       
        trimodal_weight3_label=QLabel("Pic 3:")
        trimodal_weight3_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        weights_layout.addWidget(trimodal_weight3_label)
        self.trimodal_weight3_spin = QDoubleSpinBox()
        self.trimodal_weight3_spin.setRange(0.0, 1.0)
        self.trimodal_weight3_spin.setValue(self.params.default_trimodal_weights[2])
        self.trimodal_weight3_spin.setSingleStep(0.05)
        weights_layout.addWidget(self.trimodal_weight3_spin)
        weights_group.setFixedHeight(50)
        weights_group.setLayout(weights_layout)
        param_layout.addWidget(weights_group)

        self.trimodal_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.trimodal_params_group)
       


    def create_pareto_params(self,distribution_layout):


        # Paramètres
        self.pareto_params_group = QGroupBox("Paramètres de la distribution Pareto")
        self.pareto_params_group.setVisible(False)
        param_layout = QVBoxLayout()
        
        info_label = QLabel("Distribution utile pour simuler une minorité de passagers arrivant très tôt ou très tard")
        info_label.setWordWrap(True)
        info_label.setFixedHeight(50)
        param_layout.addWidget(info_label)
        
        alpha_layout = QHBoxLayout()
        pareto_alpha_label=QLabel("Paramètre alpha (α):")
        pareto_alpha_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        alpha_layout.addWidget(pareto_alpha_label)
        self.pareto_alpha_spin = QDoubleSpinBox()
        self.pareto_alpha_spin.setRange(0.1, 5.0)
        self.pareto_alpha_spin.setValue(self.params.default_pareto_alpha)
        self.pareto_alpha_spin.setSingleStep(0.1)
        alpha_layout.addWidget(self.pareto_alpha_spin)
        param_layout.addLayout(alpha_layout)
       
        scale_layout = QHBoxLayout()
        pareto_scale_label=QLabel("Paramètre scale:")
        pareto_scale_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        scale_layout.addWidget(pareto_scale_label)
        self.pareto_scale_spin = QDoubleSpinBox()
        self.pareto_scale_spin.setRange(1.0, 100.0)
        self.pareto_scale_spin.setValue(self.params.default_pareto_scale)
        self.pareto_scale_spin.setSingleStep(1.0)
        scale_layout.addWidget(self.pareto_scale_spin)
        param_layout.addLayout(scale_layout)



        self.pareto_params_group.setLayout(param_layout)
        distribution_layout.addWidget(self.pareto_params_group)
       

    def setup_connections(self):
        """Configure les connexions entre les signaux et slots"""
        self.simul_combo.currentTextChanged.connect(self.set_curent_simulation)
        self.site_combo.currentTextChanged.connect(self.update_compagnies)
        self.date_edit.dateChanged.connect(self.update_compagnies)
        self.compagnie_list.itemSelectionChanged.connect(self.update_vols)

    def update_compagnies(self):
        """Met à jour la liste des compagnies en fonction du site et de la date sélectionnés"""
        self.update_params()
        compagnies = self.db.get_compagnies(self.params.site, self.params.date_str)
       
        # Sauvegarder les sélections actuelles
        selected_items = [item.text() for item in self.compagnie_list.selectedItems()]
       
        # Mettre à jour la liste
        self.compagnie_list.clear()
        self.compagnie_list.addItems(compagnies)
       
        # Restaurer les sélections si elles existent toujours
        for i in range(self.compagnie_list.count()):
            item = self.compagnie_list.item(i)
            if item.text() in selected_items:
                item.setSelected(True)

    def update_vols(self):
        """Met à jour la liste des vols en fonction du site, de la date et de la compagnie sélectionnés"""
        self.update_params()
        compagnie_items = [item.text() for item in self.compagnie_list.selectedItems()]
       
        if compagnie_items:  # Ne faire la mise à jour que si au moins une compagnie est sélectionnée
            vols = []
            for compagnie in compagnie_items:
                vols.extend(self.db.get_vols(self.params.site, self.params.date_str, compagnie))
           
            # Sauvegarder les sélections actuelles
            selected_items = [item.text() for item in self.num_vol_list.selectedItems()]
           
            # Mettre à jour la liste
            self.num_vol_list.clear()
            self.num_vol_list.addItems(vols)
           
            # Restaurer les sélections si elles existent toujours
            for i in range(self.num_vol_list.count()):
                item = self.num_vol_list.item(i)
                if item.text() in selected_items:
                    item.setSelected(True)
        else:
            self.num_vol_list.clear()

    def toggle_params_globaux(self):
        """Affiche ou masque les paramètres """
        # Récupérer les éléments UI correspondants

        group = self.params_globaux_group
        button = self.globaux_params_button
        fig = self.canvas
        if group.isVisible():
            group.setVisible(False)
            fig.setVisible(True)
            button.setIcon(self.icons['expand'])
            button.setText(" Paramètres")
        else:
            group.setVisible(True)
            fig.setVisible(False)
            button.setIcon(self.icons['collapse'])
            button.setText(" Masquer")
       

    def reset_params(self, dist_type):
        """Réinitialise les paramètres d'une distribution à leurs valeurs par défaut"""
        if dist_type == "globaux":
            # Réinitialiser les paramètres temporels
            self.start_hour.setValue(0)
            self.start_min.setValue(0)
            self.end_hour.setValue(23)
            self.end_min.setValue(59)
            self.step_spin.setValue(self.params.step_time)
           
            # Réinitialiser les paramètres d'enregistrement
            self.open_spin.setValue(self.params.open_min)
            self.close_spin.setValue(self.params.close_min)
           
            # Réinitialiser les paramètres bagages
            self.baggage_spin.setValue(self.params.max_bagage)
            self.poids_moyen_baggage_spin.setValue(self.params.poids_moyen_bagage)
            self.longueur_moyen_baggage_spin.setValue(self.params.longueur_moyenne_bagage)
           
            # Réinitialiser les paramètres convoyeur
            self.traitement_moyen_spin.setValue(self.params.traitement)
            self.poids_max_tapis_spin.setValue(self.params.poids_max)
            self.longueur_tapis_spin.setValue(self.params.longueur_max)
           
            # Réinitialiser les sélections de compagnie et vol
            # self.compagnie_combo.setCurrentIndex(0)
            # self.num_vol_combo.setCurrentIndex(0)
            # self.update_compagnies()

        elif dist_type == "normal":
            self.sigma_spin.setValue(self.params.default_sigma)
           
        elif dist_type == "poisson":
            self.lambda_spin.setValue(self.params.default_lambda)

        elif dist_type == "binomialnegatif":
            self.mu_spin.setValue(self.params.default_mu)
            self.k_spin.setValue(self.params.k)
           
        elif dist_type == "beta":
            self.alpha_spin.setValue(self.params.default_alpha)
            self.beta_spin.setValue(self.params.default_beta)
           
        elif dist_type == "bimodal":
            self.early_mean_spin.setValue(self.params.default_early_mean)
            self.early_std_spin.setValue(self.params.default_early_std)
            self.late_mean_spin.setValue(self.params.default_late_mean)
            self.late_std_spin.setValue(self.params.default_late_std)
            self.early_weight_slider.setValue(int(self.params.default_early_weight * 100))
            self.early_weight_label.setText(f"{self.params.default_early_weight:.2f}")
           
        elif dist_type == "lognormal":
            self.lognormal_mu_spin.setValue(self.params.default_lognormal_mu)
            self.lognormal_sigma_spin.setValue(self.params.default_lognormal_sigma)
           
        elif dist_type == "gamma":
            self.gamma_shape_spin.setValue(self.params.default_gamma_shape)
            self.gamma_scale_spin.setValue(self.params.default_gamma_scale)
           
        elif dist_type == "weibull":
            self.weibull_shape_spin.setValue(self.params.default_weibull_shape)
            self.weibull_scale_spin.setValue(self.params.default_weibull_scale)
           
        elif dist_type == "trimodal":
            self.trimodal_mean1_spin.setValue(self.params.default_trimodal_means[0])
            self.trimodal_mean2_spin.setValue(self.params.default_trimodal_means[1])
            self.trimodal_mean3_spin.setValue(self.params.default_trimodal_means[2])
           
            self.trimodal_std1_spin.setValue(self.params.default_trimodal_stds[0])
            self.trimodal_std2_spin.setValue(self.params.default_trimodal_stds[1])
            self.trimodal_std3_spin.setValue(self.params.default_trimodal_stds[2])
           
            self.trimodal_weight1_spin.setValue(self.params.default_trimodal_weights[0])
            self.trimodal_weight2_spin.setValue(self.params.default_trimodal_weights[1])
            self.trimodal_weight3_spin.setValue(self.params.default_trimodal_weights[2])
           
        elif dist_type == "pareto":
            self.pareto_alpha_spin.setValue(self.params.default_pareto_alpha)
            self.pareto_scale_spin.setValue(self.params.default_pareto_scale)

        # Message de confirmation
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)
        msg.setText(f"Les paramètres {dist_type} ont été réinitialisés")
        msg.setWindowTitle("Réinitialisation")
        msg.exec_()


    def update_params(self):
        # Paramètres de base
        self.params.site = self.site_combo.currentText()
        self.params.date_str = self.date_edit.date().toString("yyyy-MM-dd")
        # Récupérer les compagnies sélectionnées
        #self.params.compagnie = self.compagnie_combo.currentText()
        self.params.compagnies = [item.text() for item in self.compagnie_list.selectedItems()]
   
        # Récupérer les vols sélectionnés
        #self.params.num_vol = self.num_vol_combo.currentText()
        self.params.num_vols = [item.text() for item in self.num_vol_list.selectedItems()]
       
        # Paramètres temporels
        start_hour = self.start_hour.value()
        start_min = self.start_min.value()
        self.params.day_start = f"{start_hour:02d}:{start_min:02d}"
       
        end_hour = self.end_hour.value()
        end_min = self.end_min.value()
        self.params.day_end = f"{end_hour:02d}:{end_min:02d}"
       
        self.params.step_time = self.step_spin.value()
        self.params.open_min = self.open_spin.value()
        self.params.close_min = self.close_spin.value()
       
        # Paramètres bagages
        self.params.max_bagage = self.baggage_spin.value()
        self.params.poids_moyen_bagage = self.poids_moyen_baggage_spin.value()
        self.params.longueur_moyenne_bagage = self.longueur_moyen_baggage_spin.value()
       
        # Paramètres convoyeur
        self.params.traitement = self.traitement_moyen_spin.value()
        self.params.poids_max = self.poids_max_tapis_spin.value()
        self.params.longueur_max = self.longueur_tapis_spin.value()
       
        # Paramètres des distributions
        if hasattr(self, 'sigma_spin'):
            self.params.default_sigma = self.sigma_spin.value()
       
        if hasattr(self, 'lambda_spin'):
            self.params.default_lambda = self.lambda_spin.value()
       
        if hasattr(self, 'alpha_spin'):
            self.params.default_alpha = self.alpha_spin.value()
       
        if hasattr(self, 'beta_spin'):
            self.params.default_beta = self.beta_spin.value()
       
        if hasattr(self, 'early_mean_spin'):
            self.params.default_early_mean = self.early_mean_spin.value()
       
        if hasattr(self, 'early_std_spin'):
            self.params.default_early_std = self.early_std_spin.value()
       
        if hasattr(self, 'late_mean_spin'):
            self.params.default_late_mean = self.late_mean_spin.value()
       
        if hasattr(self, 'late_std_spin'):
            self.params.default_late_std = self.late_std_spin.value()
       
        if hasattr(self, 'early_weight_slider'):
            self.params.default_early_weight = self.early_weight_slider.value() / 100
       
        if hasattr(self, 'lognormal_mu_spin'):
            self.params.default_lognormal_mu = self.lognormal_mu_spin.value()
       
        if hasattr(self, 'lognormal_sigma_spin'):
            self.params.default_lognormal_sigma = self.lognormal_sigma_spin.value()
       
        if hasattr(self, 'gamma_shape_spin'):
            self.params.default_gamma_shape = self.gamma_shape_spin.value()
       
        if hasattr(self, 'gamma_scale_spin'):
            self.params.default_gamma_scale = self.gamma_scale_spin.value()
       
        if hasattr(self, 'weibull_shape_spin'):
            self.params.default_weibull_shape = self.weibull_shape_spin.value()
       
        if hasattr(self, 'weibull_scale_spin'):
            self.params.default_weibull_scale = self.weibull_scale_spin.value()
       
        if hasattr(self, 'trimodal_means_spins'):
            self.params.default_trimodal_means = [
                self.trimodal_means_spins[0].value(),
                self.trimodal_means_spins[1].value(),
                self.trimodal_means_spins[2].value()
            ]
       
        if hasattr(self, 'trimodal_stds_spins'):
            self.params.default_trimodal_stds = [
                self.trimodal_stds_spins[0].value(),
                self.trimodal_stds_spins[1].value(),
                self.trimodal_stds_spins[2].value()
            ]
       
        if hasattr(self, 'trimodal_weights_spins'):
            self.params.default_trimodal_weights = [
                self.trimodal_weights_spins[0].value() / 100,
                self.trimodal_weights_spins[1].value() / 100,
                self.trimodal_weights_spins[2].value() / 100
            ]
       
        if hasattr(self, 'pareto_alpha_spin'):
            self.params.default_pareto_alpha = self.pareto_alpha_spin.value()
       
        if hasattr(self, 'pareto_scale_spin'):
            self.params.default_pareto_scale = self.pareto_scale_spin.value()

    def get_curent_simulation(self):
        """Retourne le type de simulation actuellement sélectionné dans l'interface"""
        return self.simul_combo.currentText()

    def set_curent_simulation(self):
        """Affiche les paramètres de la distribution sélectionnée et masque les autres"""
        # Récupérer la simulation sélectionnée
        sim_type = self.simul_combo.currentText()
       
        # Masquer tous les groupes de paramètres
        self.uniform_params_group.setVisible(False)
        self.normal_params_group.setVisible(False)
        self.poisson_params_group.setVisible(False)
        self.binomialnegatif_params_group.setVisible(False)
        self.beta_params_group.setVisible(False)
        self.bimodal_params_group.setVisible(False)
        self.lognormal_params_group.setVisible(False)
        self.gamma_params_group.setVisible(False)
        self.weibull_params_group.setVisible(False)
        self.trimodal_params_group.setVisible(False)
        self.pareto_params_group.setVisible(False)
       
        # Afficher uniquement le groupe correspondant à la simulation sélectionnée
        if sim_type == "uniform":
            self.uniform_params_group.setVisible(True)
        elif sim_type == "normal":
            self.normal_params_group.setVisible(True)
        elif sim_type == "poisson":
            self.poisson_params_group.setVisible(True)
        elif sim_type == "binomialnegatif":
            self.binomialnegatif_params_group.setVisible(True)
        elif sim_type == "beta":
            self.beta_params_group.setVisible(True)
        elif sim_type == "bimodal":
            self.bimodal_params_group.setVisible(True)
        elif sim_type == "lognormal":
            self.lognormal_params_group.setVisible(True)
        elif sim_type == "gamma":
            self.gamma_params_group.setVisible(True)
        elif sim_type == "weibull":
            self.weibull_params_group.setVisible(True)
        elif sim_type == "trimodal":
            self.trimodal_params_group.setVisible(True)
        elif sim_type == "pareto":
            self.pareto_params_group.setVisible(True)

    def run_simulation(self):
        sim_type=self.get_curent_simulation()
        self.params_globaux_group.setVisible(False)
        self.canvas.setVisible(True)
        result,data,sim=self.calcul_simulation(sim_type)
        self.draw_graph_simulation(sim_type,result,data)

    def calcul_simulation(self, sim_type,params=None):
        if params is None:
            self.update_params()
            params=self.params
       
        if sim_type == "uniform":
            sim = Simulate_uniforme(params)
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "normal":
            sim = Simulate_normale(params, sigma_minutes=self.sigma_spin.value())
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "poisson":
            sim = Simulate_poisson(params, lambda_param=self.lambda_spin.value())
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "binomialnegatif":
            sim = Simulate_binomialnegatif(params, mu=self.mu_spin.value(), k=self.k_spin.value())
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "beta":
            sim = Simulate_beta(params, alpha=self.alpha_spin.value(), beta=self.beta_spin.value())
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "bimodal":
            early_weight = self.early_weight_slider.value() / 100
            sim = Simulate_bimodal(
                params,
                early_mean=self.early_mean_spin.value(),
                early_std=self.early_std_spin.value(),
                late_mean=self.late_mean_spin.value(),
                late_std=self.late_std_spin.value(),
                early_weight=early_weight
            )
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "lognormal":
            sim = Simulate_lognormale(
                params,
                mu=params.default_lognormal_mu,
                sigma=params.default_lognormal_sigma
            )
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "gamma":
            sim = Simulate_gamma(
                params,
                shape=params.default_gamma_shape,
                scale=params.default_gamma_scale
            )
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "weibull":
            sim = Simulate_weibull(
                params,
                shape=params.default_weibull_shape,
                scale=params.default_weibull_scale
            )
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "trimodal":
            sim = Simulate_trimodal(
                params,
                means=params.default_trimodal_means,
                stds=params.default_trimodal_stds,
                weights=params.default_trimodal_weights
            )
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim
        elif sim_type == "pareto":
            sim = Simulate_pareto(
                params,
                alpha=params.default_pareto_alpha,
                scale=params.default_pareto_scale
            )
            result = sim.run()
            data = sim.simulate(result)
            return result, data, sim

    def draw_graph_simulation(self, sim_type,result,data):
       
        if sim_type == "uniform":
            title= "Distribution uniforme"
        elif sim_type == "normal":
            title="Distribution normale"
        elif sim_type == "poisson":
            title="Distribution exponentielle"
        elif sim_type == "binomialnegatif":
            title="Distribution Binomiale Négative"
        elif sim_type == "beta":
            title="Distribution Beta"
        elif sim_type == "bimodal":
            title="Distribution bimodale"
        elif sim_type == "lognormal":
            title="Distribution lognormale"
        elif sim_type == "gamma":
            title="Distribution gamma"
        elif sim_type == "weibull":
            title="Distribution weibulle"
        elif sim_type == "trimodal":
            title="Distribution trimodale"
        elif sim_type == "pareto":
            title="Distribution paretoe"
        else:
            return
        self.plot_results(self.fig, result,data, title,
                             self.vols_check,self.manutentionnaires_check,self.enregistrements_check, self.voyageurs_check, self.bagages_check,
                             self.tapis_check1,self.tapis_check2,self.tapis_check3,self.tapis_check4,self.tapis_check5)

    def plot_results(self, fig, results, data, title,vols_check,manutentionnaires_check, enregistrements_check, voyageurs_check, bagages_check, tapis_check1,tapis_check2,tapis_check3,tapis_check4,tapis_check5):
        """Affiche les résultats dans une figure matplotlib selon les cases cochées"""
        fig.clear()
       
        # Simplifier les étiquettes d'axe x (juste les heures)
        times = results["times"]
        simplified_times = []
        prev_hour = ""
        for t in times:
            hour = t.split(":")[0]
            if hour != prev_hour:
                simplified_times.append(f"{hour}h")
                prev_hour = hour
            else:
                simplified_times.append("")
       
        # Déterminer le nombre de graphes à afficher
        num_plots = sum([vols_check.isChecked(),manutentionnaires_check.isChecked(),enregistrements_check.isChecked(), voyageurs_check.isChecked(), bagages_check.isChecked(),
                        tapis_check1.isChecked(),tapis_check2.isChecked(),tapis_check3.isChecked(),tapis_check4.isChecked(),tapis_check5.isChecked()])
        if num_plots == 0:
            return

        plot_index = 1
       
        # Fonction pour créer des infobulles pour les barres
        def create_bar_tooltip(ax, x_data, y_data, label):
            annot = ax.annotate("", xy=(0,0), xytext=(20,-40), textcoords="offset points",
                              bbox=dict(boxstyle="round", fc="w"),
                              arrowprops=dict(arrowstyle="->"))
            annot.set_visible(False)
           
            def update_annot(bar, idx):
                x = bar.get_x() + bar.get_width() / 2
                y = bar.get_height()
                annot.xy = (x, y)
                text = f"{label}: {y:.0f}\nHeure: {x_data[idx]}"
                annot.set_text(text)
                annot.get_bbox_patch().set_alpha(1)
               
            def hover(event):
                if event.inaxes == ax:
                    vis = False
                    for i, bar in enumerate(ax.patches):
                        cont, _ = bar.contains(event)
                        if cont:
                            update_annot(bar, i)
                            annot.set_visible(True)
                            fig.canvas.draw_idle()
                            vis = True
                            break
                    if not vis:
                        annot.set_visible(False)
                        fig.canvas.draw_idle()
                   
            fig.canvas.mpl_connect("motion_notify_event", hover)
       
        # Graphique des vols
        if vols_check.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            vols=[len(result) for result in results["vols"]]
            ax.bar(results["times"], vols, color='purple')
            ax.set_title(f"Nombre de vols par tranche horaire")
            ax.set_ylabel("Nombre de vol")
            ax.set_xticklabels(simplified_times)
            ax.grid(True, linestyle='--', alpha=0.7)
            create_bar_tooltip(ax, results["times"], vols, "vol")
            plot_index += 1

       # Graphique des manutentionnaires_check
        if manutentionnaires_check.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            manutentionnaires=[len(result) for result in results["manutentionnaires"]]
            ax.bar(results["times"], manutentionnaires, color='pink')
            ax.set_title(f"Nombre de manutentionnaires par tranche horaire")
            ax.set_ylabel("Nombre de manutentionnaires")
            ax.set_xticklabels(simplified_times)
            ax.grid(True, linestyle='--', alpha=0.7)
            create_bar_tooltip(ax, results["times"], manutentionnaires, "vol")
            plot_index += 1

        # Graphique des enregistrements
        if enregistrements_check.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            enregistrements=[len(result) for result in results["enregistrements"]]
            ax.bar(results["times"], enregistrements, color='green')
            ax.set_title(f"Nombre d'enregistrement par tranche horaire")
            ax.set_ylabel("Nombre d'enregistrement")
            ax.set_xticklabels(simplified_times)
            ax.grid(True, linestyle='--', alpha=0.7)
            create_bar_tooltip(ax, results["times"], enregistrements, "Enregistrement")
            plot_index += 1
       
        # Graphique des voyageurs
        if voyageurs_check.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            voyageurs=[len(result) for result in results["voyageurs"]]
            ax.bar(results["times"], voyageurs, color='olive')
            ax.set_title(f"{title} - Flux de voyageurs")
            ax.set_ylabel("Nombre de voyageurs")
            ax.set_xticklabels(simplified_times)
            ax.grid(True, linestyle='--', alpha=0.7)
            create_bar_tooltip(ax, results["times"], voyageurs, "Voyageurs")
            plot_index += 1
       
        # Graphique des bagages
        if bagages_check.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            bagages=[sum(bagage[1] for bagage in result) for result in results["bagages"]]
            ax.bar(results["times"], bagages, color='brown')
            ax.set_title(f"{title} - Flux de bagages")
            ax.set_ylabel("Nombre de bagages")
            ax.set_xlabel("Heure de la journée")
            ax.set_xticklabels(simplified_times)
            ax.grid(True, linestyle='--', alpha=0.7)
            create_bar_tooltip(ax, results["times"], bagages, "Bagages")
            plot_index += 1
       
        # Graphique des tapis
        if tapis_check1.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            tapis='Zone A caroussel 1'
            self.draw_graph_caroussel(tapis,title,simplified_times,fig,ax,data["caroussel_1"])
            plot_index += 1
        if tapis_check2.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            tapis='Zone A caroussel 2'
            self.draw_graph_caroussel(tapis,title,simplified_times,fig,ax,data["caroussel_2"])
            plot_index += 1
        if tapis_check3.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            tapis='Zone B caroussel 1'
            self.draw_graph_caroussel(tapis,title,simplified_times,fig,ax,data["caroussel_3"])
            plot_index += 1
        if tapis_check4.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            tapis='Zone B caroussel 2'
            self.draw_graph_caroussel(tapis,title,simplified_times,fig,ax,data["caroussel_4"])
            plot_index += 1
        if tapis_check5.isChecked():
            ax = fig.add_subplot(num_plots, 1, plot_index)
            tapis='Zone B caroussel 3'
            self.draw_graph_caroussel(tapis,title,simplified_times,fig,ax,data["caroussel_5"])
            plot_index += 1

        fig.tight_layout()
        fig.canvas.draw()



    def draw_graph_caroussel(self,tapis,title,simplified_times,fig,ax,data):
        line_rejet, =ax.plot(data['times'], data['Bagages_rejetes'], label='Bagages rejeté', color='red')
        line_tratement, = ax.plot(data["times"], data['Bagages_sur_tapis'], label='Bagages sur tapis', color='blue')
       
        capacite_longueur = self.params.longueur_max / self.params.longueur_moyenne_bagage
        capacite_poids = self.params.poids_max / self.params.poids_moyen_bagage
        ax.axhline(y=capacite_longueur, color='orange', linestyle='--', label='Capacité max (longueur)')
        ax.axhline(y=capacite_poids, color='purple', linestyle='--', label='Capacité max (poids)')
       
        # Marquage des périodes d'échec
        for i in range(len(data['Echec'])):
            if data['Echec'][i]:
                ax.axvline(x=data["times"][i], color='orange', alpha=0.3)

        # Infobulle pour le graphique des tapis
        annot = ax.annotate("", xy=(0,0), xytext=(20,-40), textcoords="offset points",
                            bbox=dict(boxstyle="round", fc="w"),
                            arrowprops=dict(arrowstyle="->"))
        annot.set_visible(False)
       
        def update_annot(ind):
            x, y = line_tratement.get_data()
            annot.xy = (x[ind], y[ind])
            text = f"Bagages: {y[ind]:.0f}\nHeure: {x[ind]}"
            if data['Echec'][ind]:
                text += "\n(Saturation)"
            annot.set_text(text)
            annot.get_bbox_patch().set_alpha(1)
           
        def hover(event):
            if event.inaxes == ax:
                cont, ind = line_tratement.contains(event)
                if cont:
                    update_annot(ind['ind'][0])
                    annot.set_visible(True)
                    fig.canvas.draw_idle()
                else:
                    annot.set_visible(False)
                    fig.canvas.draw_idle()
                   
        fig.canvas.mpl_connect("motion_notify_event", hover)

        ax.set_title(f"{title} - {tapis} Simulation de la charge du tapis convoyeur et des périodes de saturation")
        ax.set_ylabel("Nombre de bagages sur le tapis")
        ax.set_xlabel("Heure de la journée")
        ax.set_xticklabels(simplified_times)
        #ax.legend()
        ax.grid(True, linestyle='--', alpha=0.7)

#-------------------------------------------------------------------------------------------------
    def export_to_csv(self):
        sim_type=self.get_curent_simulation()
        results,data,sim=self.calcul_simulation(sim_type)
        filename, _ = QFileDialog.getSaveFileName(self, "Exporter en CSV", "", "CSV Files (*.csv)")
       
        if filename:
            if not filename.endswith('.csv'):
                filename += '.csv'
           
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                writer.writerow(['Heure',
                                'Enregistrements',
                                'Voyageurs',
                                'Bagages',
                                'caroussel_1_Bagages_sur_tapis',
                                'caroussel_1_Poids_sur_tapis',
                                'caroussel_1_Longueur_sur_tapis',
                                'caroussel_1_Bagages_rejetes',
                                'caroussel_1_Echec',
                                'caroussel_1_Poids_depasse',
                                'caroussel_1_Longueur_depasse',
                                'caroussel_2_Bagages_sur_tapis',
                                'caroussel_2_Poids_sur_tapis',
                                'caroussel_2_Longueur_sur_tapis',
                                'caroussel_2_Bagages_rejetes',
                                'caroussel_2_Echec',
                                'caroussel_2_Poids_depasse',
                                'caroussel_2_Longueur_depasse',
                                'caroussel_3_Bagages_sur_tapis',
                                'caroussel_3_Poids_sur_tapis',
                                'caroussel_3_Longueur_sur_tapis',
                                'caroussel_3_Bagages_rejetes',
                                'caroussel_3_Echec',
                                'caroussel_3_Poids_depasse',
                                'caroussel_3_Longueur_depasse'
                                ])
                enregistrements=[len(result) for result in results["enregistrements"]]
                voyageurs=[len(result) for result in results["voyageurs"]]
                bagages=[sum(bagage[1] for bagage in result) for result in results["bagages"]]
                for i in range(len(results["times"])):
                    writer.writerow([
                                    results["times"][i],
                                    enregistrements[i],
                                    voyageurs[i],
                                    bagages[i],
                                    data["caroussel_1"]["Bagages_sur_tapis"][i],
                                    data["caroussel_1"]["Poids_sur_tapis"][i],
                                    data["caroussel_1"]["Longueur_sur_tapis"][i],
                                    data["caroussel_1"]["Bagages_rejetes"][i],
                                    data["caroussel_1"]["Echec"][i],
                                    data["caroussel_1"]["Poids_depasse"][i],
                                    data["caroussel_1"]["Longueur_depasse"][i],
                                    data["caroussel_2"]["Bagages_sur_tapis"][i],
                                    data["caroussel_2"]["Poids_sur_tapis"][i],
                                    data["caroussel_2"]["Longueur_sur_tapis"][i],
                                    data["caroussel_2"]["Bagages_rejetes"][i],
                                    data["caroussel_2"]["Echec"][i],
                                    data["caroussel_2"]["Poids_depasse"][i],
                                    data["caroussel_2"]["Longueur_depasse"][i],
                                    data["caroussel_3"]["Bagages_sur_tapis"][i],
                                    data["caroussel_3"]["Poids_sur_tapis"][i],
                                    data["caroussel_3"]["Longueur_sur_tapis"][i],
                                    data["caroussel_3"]["Bagages_rejetes"][i],
                                    data["caroussel_3"]["Echec"][i],
                                    data["caroussel_3"]["Poids_depasse"][i],
                                    data["caroussel_3"]["Longueur_depasse"][i]
                                    ])
#-----------------------------------------------------------------------------------------------
    def visualise_simulation(self):
        # Récupérer les données de simulation
        sim_type=self.get_curent_simulation()
        result, data,sim = self.calcul_simulation(sim_type)
        self.sim_data = data
        self.result_data = result  

        # Créer une nouvelle fenêtre pour la visualisation
        self.vis_window = QMainWindow()  # Stocker la référence dans self
        self.vis_window.setWindowTitle(f"Visualisation Carrousel - {sim_type}")
        self.vis_window.setGeometry(100, 100, 800, 600)
       
        central_widget = QWidget()
        self.vis_window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
       
        # Sélection du carrousel
        carrousel_group = QGroupBox("Paramètres de visualisation")
        carrousel_layout = QHBoxLayout()
       
        carrousel_layout.addWidget(QLabel("Carrousel:"))
        self.carrousel_combo = QComboBox()
        self.carrousel_combo.addItems(["Zone A-1", "Zone A-2", "Zone B-1", "Zone B-2", "Zone B-3"])
        carrousel_layout.addWidget(self.carrousel_combo)
       
        # Slider pour contrôler le temps
        self.time_slider = QSlider(Qt.Horizontal)
        self.time_slider.setRange(0, len(result["times"])-1)
        self.time_slider.setTickInterval(1)
        self.time_slider.setTickPosition(QSlider.TicksBelow)
        carrousel_layout.addWidget(self.time_slider)
       
        # Contrôle de vitesse (nouveau)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(QLabel("Vitesse:"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["Lent", "Normal", "Rapide", "Très rapide"])
        self.speed_combo.setCurrentText("Normal")
        speed_layout.addWidget(self.speed_combo)
        carrousel_layout.addLayout(speed_layout)
       
        # Boutons de contrôle
        control_layout = QHBoxLayout()
       
        self.play_button = QPushButton(self.icons['play'], "")
        self.pause_button = QPushButton(self.icons['pause'], "")
        self.stop_button = QPushButton(self.icons['stop'], "")
       
        control_layout.addWidget(self.play_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)
       
        carrousel_layout.addLayout(control_layout)
        carrousel_group.setLayout(carrousel_layout)
        main_layout.addWidget(carrousel_group)
       
        # Création du splitter pour diviser l'espace
        splitter = QSplitter(Qt.Vertical)
       
        # Zone de visualisation du carrousel (3/4 de l'espace)
        carrousel_container = QWidget()
        carrousel_container_layout = QVBoxLayout(carrousel_container)
        self.carrousel_view = QGraphicsView()
        self.carrousel_scene = QGraphicsScene()
        self.carrousel_view.setScene(self.carrousel_scene)
        self.carrousel_view.setRenderHint(QPainter.Antialiasing)
        carrousel_container_layout.addWidget(self.carrousel_view)
        splitter.addWidget(carrousel_container)
       
        # Graphique de charge du carrousel (1/4 de l'espace)
        charge_container = QWidget()
        charge_container_layout = QVBoxLayout(charge_container)
        self.charge_fig = Figure()
        self.charge_canvas = FigureCanvas(self.charge_fig)
        charge_container_layout.addWidget(self.charge_canvas)
        splitter.addWidget(charge_container)
       
        # Définir les proportions initiales (3/4 pour le carrousel, 1/4 pour le graphique)
        splitter.setSizes([600, 200])  # Valeurs approximatives pour une fenêtre de 800x600
       
        main_layout.addWidget(splitter)
       
        # Données pour l'animation
        self.current_frame = 0
        self.timer = QTimer()
       
        # Dictionnaire des vitesses possibles (intervalle en ms)
        self.speed_options = {
            "Lent": 2000,      # 2 secondes
            "Normal": 1000,    # 1 seconde (défaut)
            "Rapide": 500,     # 0.5 seconde
            "Très rapide": 250 # 0.25 seconde
        }
        self.timer.setInterval(self.speed_options["Normal"])  # Valeur par défaut
       
        # Connexions des signaux
        def update_carrousel(frame):
            self.current_frame = frame
            self.time_slider.setValue(frame)
            self.draw_carrousel_animation(frame)
            self.draw_charge_graph(frame)
       
        self.time_slider.valueChanged.connect(update_carrousel)
       
        def play_animation():
            # Mettre à jour l'intervalle selon la sélection
            speed_text = self.speed_combo.currentText()
            self.timer.setInterval(self.speed_options[speed_text])
            self.timer.start()
       
        def pause_animation():
            self.timer.stop()
       
        def stop_animation():
            self.timer.stop()
            update_carrousel(0)
       
        self.play_button.clicked.connect(play_animation)
        self.pause_button.clicked.connect(pause_animation)
        self.stop_button.clicked.connect(stop_animation)
       
        self.timer.timeout.connect(lambda: update_carrousel(
            (self.current_frame + 1) % len(result["times"]))
        )
       
        # Initialisation
        self.carrousel_combo.currentTextChanged.connect(
            lambda: update_carrousel(self.current_frame)
        )
       
        # Afficher la fenêtre
        self.vis_window.show()
        update_carrousel(0)

    def draw_carrousel_animation(self, frame):
        self.carrousel_scene.clear()
        # Récupération des données
        carrousel_num = self.carrousel_combo.currentIndex() + 1
        current_time = self.result_data['times'][frame]
        caroussel = f"caroussel_{carrousel_num}"
        num_bags = self.sim_data[caroussel]['Bagages_sur_tapis'][frame]
        poids_sur_tapis= self.sim_data[caroussel]['Poids_sur_tapis'][frame]
        longueur_sur_tapis= self.sim_data[caroussel]['Longueur_sur_tapis'][frame]
        handlers_data=list(filter(lambda x: x is not None, [ handler[0] if( handler[1] == carrousel_num) else None   for handler in self.result_data['manutentionnaires'][frame]]))
        echec = self.sim_data[caroussel]['Echec'][frame]
        poids_depasse = self.sim_data[caroussel]['Poids_depasse'][frame]
        longueur_depasse = self.sim_data[caroussel]['Longueur_depasse'][frame]
        bagages_rejetes = self.sim_data[caroussel]['Bagages_rejetes'][frame]

        # Dimensions
        scene_width = self.carrousel_view.width()
        scene_height = self.carrousel_view.height()
        center_x, center_y = scene_width // 2, scene_height // 2
       
        # Paramètres de l'hippodrome
        outer_width = min(600, scene_width - 40)  # Ajuster à la taille de la vue
        outer_height = min(300, scene_height - 40)
        outer_radius = outer_height // 2
        belt_width = 50  # Largeur de la bande transporteuse
       
        # 1. Structure de l'hippodrome (contour extérieur)
        path = QPainterPath()
        # Rectangle central
        path.addRect(center_x - outer_width//2, center_y - outer_radius, outer_width, outer_height)
        # Demi-cercles
        path.moveTo(center_x - outer_width//2, center_y)
        path.arcTo(center_x - outer_width//2 - outer_radius, center_y - outer_radius,
                  outer_radius*2, outer_radius*2, 90, 180)
        path.moveTo(center_x + outer_width//2, center_y)
        path.arcTo(center_x + outer_width//2 - outer_radius, center_y - outer_radius,
                  outer_radius*2, outer_radius*2, 270, 180)
       
        hippodrome = QGraphicsPathItem(path)
        hippodrome.setBrush(QBrush(QColor(180, 180, 180)))
        hippodrome.setPen(QPen(Qt.darkGray, 3))
        self.carrousel_scene.addItem(hippodrome)

        # 2. Bande transporteuse (périmètre intérieur)
        inner_width = outer_width - 2*belt_width
        inner_height = outer_height - 2*belt_width
        inner_radius = inner_height // 2
       
        belt_path = QPainterPath()
        # Rectangle central de la bande
        belt_path.addRect(center_x - inner_width//2, center_y - inner_radius, inner_width, inner_height)
        # Demi-cercles de la bande
        belt_path.moveTo(center_x - inner_width//2, center_y)
        belt_path.arcTo(center_x - inner_width//2 - inner_radius, center_y - inner_radius,
                       inner_radius*2, inner_radius*2, 90, 180)
        belt_path.moveTo(center_x + inner_width//2, center_y)
        belt_path.arcTo(center_x + inner_width//2 - inner_radius, center_y - inner_radius,
                       inner_radius*2, inner_radius*2, 270, 180)
       
        belt = QGraphicsPathItem(belt_path)
        if echec:
            belt.setBrush(QBrush(QColor(225, 0, 0)))  
        else:
            belt.setBrush(QBrush(QColor(0, 225, 0)))  

        belt.setPen(QPen(Qt.darkGray, 1))
        self.carrousel_scene.addItem(belt)

        inner_radius = outer_height // 2

        # 3. Bagages SUR la bande transporteuse (positionnement précis)
        max_visible_bags = min(30, num_bags)
        belt_length = 2 * inner_width + 2 * math.pi * inner_radius  # Périmètre total
       
        for i in range(max_visible_bags):
            # Position le long de la bande (0-1)
            pos_ratio = (i / max_visible_bags + frame/len(self.result_data["times"])) % 1
           
            # Déterminer sur quelle partie de la bande nous sommes
            if pos_ratio < 0.25:  # Côté droit
                x = center_x - inner_width//2 + inner_width * (pos_ratio / 0.25)
                y = center_y - inner_radius +20
                angle = 0
            elif pos_ratio < 0.5:  # Demi-cercle bas
                angle = math.pi * ((pos_ratio - 0.25) / 0.25)
                x = center_x + inner_width//2 + inner_radius * math.sin(angle)+20
                y = center_y - inner_radius * math.cos(angle)+10
                angle = math.degrees(angle)
            elif pos_ratio < 0.75:  # Côté bas rectangle
                x = center_x + inner_width//2 - inner_width * ((pos_ratio - 0.5) / 0.25)
                y = center_y + inner_radius
                angle = 180
            else:  # Demi-cercle haut
                angle =  math.pi * ((pos_ratio - 0.25) / 0.25)
                x = center_x - inner_width//2 - inner_radius * math.sin(angle)
                y = center_y - inner_radius * math.cos(angle) +10
                angle = math.degrees(angle)
           
            # Dessin du bagage
            if i % 2 == 0:
                # Valise
                suitcase = QGraphicsRectItem(0, 0, 24, 16)
                suitcase.setPos(x - 12, y - 8)
                suitcase.setBrush(QBrush(QColor(139, 69, 19)))
                suitcase.setRotation(angle)
                self.carrousel_scene.addItem(suitcase)
            else:
                # Sac à dos
                backpack = QGraphicsEllipseItem(0, 0, 16, 24)
                backpack.setPos(x - 8, y - 12)
                backpack.setBrush(QBrush(QColor(30, 60, 120)))
                backpack.setRotation(angle)
                self.carrousel_scene.addItem(backpack)

        # 4. Manutentionnaires autour du carrousel
        handler_distance = outer_width//2 + 20  # Réduire la distance pour être juste à l'extérieur du carrousel

        if handlers_data:  # Vérifier qu'il y a des handlers à afficher
            # Calculer l'angle entre chaque handler
            max_visible_handlers =len(handlers_data)
            angle_step = 2 * math.pi / max_visible_handlers
            actions=["prendre","porter","pousser"]
            for i, handler in enumerate(handlers_data):
                handler_name = handler
                handler_action = "prendre" if  (num_bags==0)  else actions[random.randint(0, 2)]
               
                pos_ratio = (i / max_visible_handlers ) % 1
               
                # Déterminer sur quelle partie de la bande nous sommes
                if pos_ratio <= 0.25:   # Côté haut rectangle
                    x = center_x - inner_width//2 + inner_width * (pos_ratio / 0.25)
                    y = center_y - inner_radius -40
                    angle = 0
                elif pos_ratio <= 0.37:  # Demi-cercle droite superieur
                    angle = math.pi * ((pos_ratio - 0.25) / 0.25)
                    x = center_x + inner_width//2 + inner_radius * math.sin(angle)+80
                    y = center_y - inner_radius * math.cos(angle)-40
                    angle = math.degrees(angle)
                elif pos_ratio <= 0.5:  # Demi-cercle droite inferieur
                    angle = math.pi * ((pos_ratio - 0.25) / 0.25)
                    x = center_x + inner_width//2 + inner_radius * math.sin(angle)+80
                    y = center_y - inner_radius * math.cos(angle)+40
                    angle = math.degrees(angle)
                elif pos_ratio <= 0.75:  # Côté bas rectangle
                    x = center_x + inner_width//2 - inner_width * ((pos_ratio - 0.5) / 0.25) +60
                    y = center_y + inner_radius +40
                    angle = 180
                elif pos_ratio <= 0.87:  # Demi-cercle gauche inferieur
                    angle =  math.pi * ((pos_ratio - 0.25) / 0.25)
                    x = center_x - inner_width//2 - (inner_radius+80) * math.sin(angle)
                    y = center_y + (inner_radius+80) * math.cos(angle)  
                    angle = math.degrees(angle)+180  
                else:  # Demi-cercle gauche superieur
                    angle =  math.pi * ((pos_ratio - 0.25) / 0.25)
                    x = center_x - inner_width//2 - (inner_radius+80) * math.sin(angle)  
                    y = center_y + (inner_radius+80) * math.cos(angle)  
                    angle = math.degrees(angle)  +180

               
                # Dessin avec orientation selon la position
                self.draw_handler(x, y, handler_action, handler_name, angle)

        poids_sur_tapis= self.sim_data[caroussel]['Poids_sur_tapis'][frame]
        longueur_sur_tapis= self.sim_data[caroussel]['Longueur_sur_tapis'][frame]


        # 5. Affichage des informations
        info_text = f"{current_time} - Carrousel {carrousel_num}\n"
        info_text += f"Bagages: {num_bags}\n"
        info_text += f"Manutentionnaires: {len(handlers_data)}\n"
        info_text += f"Poids sur tapis(kg): {poids_sur_tapis}\n"
        info_text += f"Longueur sur tapis(m): {longueur_sur_tapis}\n"

        info_label = QGraphicsTextItem(info_text)
        info_label.setPos( center_x-100, center_y-60)
        info_label.setFont(QFont("Arial", 10, QFont.Bold))
        self.carrousel_scene.addItem(info_label)

    def draw_handler(self, x, y, action, name, rotation):
        """Dessin précis d'un manutentionnaire orienté"""
        #rotation = math.degrees(angle)
        handler_group = QGraphicsItemGroup()
       
        # Tête
        head = QGraphicsEllipseItem(-10, -25, 20, 20, handler_group)
        head.setBrush(QBrush(QColor(255, 218, 185)))
       
        # Corps
        body = QGraphicsRectItem(-10, 0, 20, 30, handler_group)
        body.setBrush(QBrush(QColor(60, 60, 150)))
       
        # Nom
        name_label = QGraphicsSimpleTextItem(name, handler_group)
        name_label.setPos(-name_label.boundingRect().width()/2, -40)
        name_label.setFont(QFont("Arial", 8))
       
        # Actions
        if action == "prendre":
            arm = QGraphicsLineItem(-10, 5, -30, -10, handler_group)
            arm.setPen(QPen(QColor(255, 218, 185), 5))
        elif action == "porter":
            arm1 = QGraphicsLineItem(-10, 5, -25, 15, handler_group)
            arm1.setPen(QPen(QColor(255, 218, 185), 5))
            arm2 = QGraphicsLineItem(10, 5, 25, 15, handler_group)
            arm2.setPen(QPen(QColor(255, 218, 185), 5))
            luggage = QGraphicsRectItem(-20, 15, 40, 15, handler_group)
            luggage.setBrush(QBrush(QColor(139, 69, 19)))
        elif action == "pousser":
            arm = QGraphicsLineItem(10, 5, 30, 15, handler_group)
            arm.setPen(QPen(QColor(255, 218, 185), 5))
            cart = QGraphicsRectItem(15, 15, 30, 15, handler_group)
            cart.setBrush(QBrush(Qt.lightGray))
       
        # Positionnement final
        handler_group.setPos(x, y)
        handler_group.setRotation(rotation)
        self.carrousel_scene.addItem(handler_group)

    def draw_charge_graph(self, frame):
        self.charge_fig.clear()
        ax = self.charge_fig.add_subplot(111)
       
        carrousel_num = self.carrousel_combo.currentIndex()+1
        carrousel_data = self.sim_data[f"caroussel_{carrousel_num}"]
       
        # Tracer l'historique de charge
        times = self.result_data["times"]
        bags = carrousel_data["Bagages_sur_tapis"]
        ax.plot(times[:frame+1], bags[:frame+1], 'b-', label='Bagages sur tapis')
       
        # Lignes de capacité
        capacite_longueur = self.params.longueur_max / self.params.longueur_moyenne_bagage
        capacite_poids = self.params.poids_max / self.params.poids_moyen_bagage
        ax.axhline(y=capacite_longueur, color='orange', linestyle='--', label='Capacité max (longueur)')
        ax.axhline(y=capacite_poids, color='purple', linestyle='--', label='Capacité max (poids)')
       
        # Point actuel
        ax.plot(times[frame], bags[frame], 'ro', markersize=8)
       
        # Mise en forme
        ax.set_title(f"Charge du carrousel {carrousel_num} au fil du temps")
        ax.set_ylabel("Nombre de bagages")
        ax.set_xlabel("Heure")
        ax.grid(True)
       
        # Simplifier les étiquettes d'axe x (juste les heures)
        simplified_times = []
        prev_hour = ""
        for t in times[:frame+1]:
            hour = t.split(":")[0]
            if hour != prev_hour:
                simplified_times.append(f"{hour}h")
                prev_hour = hour
            else:
                simplified_times.append("")
       
        # Appliquer les étiquettes simplifiées
        ax.set_xticks(range(len(times[:frame+1])))
        ax.set_xticklabels(simplified_times)
       
        # Rotation des étiquettes x pour plus de lisibilité
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
       
        self.charge_fig.tight_layout()
        self.charge_canvas.draw()

    def show_info(self, sim_type):
        """Affiche les informations sur le mode de simulation avec les détails du fichier simulation.py"""
        if sim_type == "":
            sim_type = self.simul_combo.currentText()
        if sim_type == "globaux":
            title = "Informations sur l'application"
            info = self.params.info_globaux
        elif sim_type == "uniform":
            title = "Distribution Uniforme"
            info = self.params.info_uniform

        elif sim_type == "normal":
            title = "Distribution Normale (Gaussienne)"
            info = self.params.info_normal
 
        elif sim_type == "poisson":
            title = "Distribution Exponentielle (Processus de Poisson)"
            info = self.params.info_poisson

        elif sim_type == "binomialnegatif":
            title = "Distribution Binomiale Négative"
            info = self.params.info_binomialnegatif
 
        elif sim_type == "beta":
            title = "Distribution Beta"
            info = self.params.info_beta

        elif sim_type == "bimodal":
            title = "Distribution Bimodale"
            info = self.params.info_bimodal
    
       
        elif sim_type == "lognormal":
            title = "Distribution Log-normale"
            info = self.params.info_lognormal

        elif sim_type == "gamma":
            title = "Distribution Gamma"
            info = self.params.info_gamma
       
        elif sim_type == "weibull":
            title = "Distribution de Weibull"
            info = self.params.info_weibull
 
        elif sim_type == "trimodal":
            title = "Distribution Tri-modale"
            info = self.params.info_trimodal

        elif sim_type == "pareto":
            title = "Distribution Pareto"
            info = self.params.info_pareto
       
        # Création de la boîte de message
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(info)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec_()
#-----------------------------------------------------------------------------------
    def edit_compagnie(self):
        """Ouvre une fenêtre pour éditer la table des compagnies et leurs affectations aux carrousels"""
        # Créer une nouvelle fenêtre pour l'édition
        edit_window = QMainWindow()
        edit_window.setWindowTitle("Édition des compagnies/carrousels")
        edit_window.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        edit_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Récupérer les données actuelles de la table compagnies
        compagnies_data = self.db.get_compagnies_all()
        
        # Créer un modèle de table
        self.compagnies_model = QStandardItemModel()
        self.compagnies_model.setHorizontalHeaderLabels(["Compagnie", "Zone", "Carrousel"])
         
        # Remplir le modèle avec les données
        for row in compagnies_data:
            
            compagnie_item = QStandardItem(row[0])
            zone_item = QStandardItem(row[1])
            carrousel_item = QStandardItem(str(row[2]))
            
            # Rendre les éléments éditables
            compagnie_item.setEditable(False)  # On ne modifie pas le nom de la compagnie
            zone_item.setEditable(True)
            carrousel_item.setEditable(True)
            
            self.compagnies_model.appendRow([compagnie_item, zone_item, carrousel_item])
         
        
        # Créer une vue table pour afficher le modèle
        table_view = QTableView()
        table_view.setModel(self.compagnies_model)
        
         
        # Configurer des délégués pour la validation des données
        # Délégué pour la zone (A ou B)
        zone_delegate = ZoneDelegate()
        table_view.setItemDelegateForColumn(1, zone_delegate)
        
         
        # Délégué pour le carrousel (dépend de la zone)
        #carrousel_delegate = CarrouselDelegate()
        #table_view.setItemDelegateForColumn(2, carrousel_delegate)
        
        # Connecter le changement de zone pour mettre à jour les valeurs possibles du carrousel
        self.compagnies_model.dataChanged.connect(self.update_carrousel_values)
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        save_button = QPushButton("Enregistrer")
        save_button.clicked.connect(lambda: self.save_compagnies_changes(edit_window))
        button_layout.addWidget(save_button)
        
        cancel_button = QPushButton("Annuler")
        cancel_button.clicked.connect(edit_window.close)
        button_layout.addWidget(cancel_button)
        
        add_button = QPushButton("Ajouter compagnie")
        add_button.clicked.connect(self.add_compagnie)
        button_layout.addWidget(add_button)
        
        remove_button = QPushButton("Supprimer compagnie")
        remove_button.clicked.connect(self.remove_compagnie)
        button_layout.addWidget(remove_button)
        
        layout.addWidget(table_view)
        layout.addLayout(button_layout)
        
        # Stocker la référence à la table view
        self.compagnies_table_view = table_view
        
        edit_window.show()

    def update_carrousel_values(self, top_left, bottom_right):
        """Met à jour les valeurs possibles du carrousel lorsque la zone change"""
        for row in range(top_left.row(), bottom_right.row() + 1):
            zone_item = self.compagnies_model.item(row, 1)
            carrousel_item = self.compagnies_model.item(row, 2)
            
            if zone_item and carrousel_item:
                zone = zone_item.text().upper()
                current_carrousel = carrousel_item.text()
                
                # Valider la zone
                if zone not in ['A', 'B']:
                    zone_item.setText('A')  # Valeur par défaut
                    zone = 'A'
                
                # Valider le carrousel en fonction de la zone
                if zone == 'A':
                    if current_carrousel not in ['1', '2']:
                        carrousel_item.setText('1')
                else:  # zone B
                    if current_carrousel not in ['3', '4', '5']:
                        carrousel_item.setText('3')

    def add_compagnie(self):
        """Ajoute une nouvelle ligne pour une nouvelle compagnie"""
        compagnie_item = QStandardItem("Nouvelle compagnie")
        zone_item = QStandardItem("A")
        carrousel_item = QStandardItem("1")
        
        compagnie_item.setEditable(True)
        zone_item.setEditable(True)
        carrousel_item.setEditable(True)
        
        self.compagnies_model.appendRow([compagnie_item, zone_item, carrousel_item])
        
        # Sélectionner la nouvelle ligne
        self.compagnies_table_view.scrollToBottom()
        self.compagnies_table_view.setCurrentIndex(self.compagnies_model.index(self.compagnies_model.rowCount() - 1, 0))
        
        # Ouvrir l'édition du nom
        self.compagnies_table_view.edit(self.compagnies_model.index(self.compagnies_model.rowCount() - 1, 0))

    def remove_compagnie(self):
        """Supprime la compagnie sélectionnée"""
        selected = self.compagnies_table_view.currentIndex()
        if selected.isValid():
            self.compagnies_model.removeRow(selected.row())

    def save_compagnies_changes(self, window):
        """Enregistre les modifications dans la base de données"""
        # Récupérer toutes les données du modèle
        compagnies = []
        for row in range(self.compagnies_model.rowCount()):
            compagnie = self.compagnies_model.item(row, 0).text()
            zone = self.compagnies_model.item(row, 1).text().upper()
            carrousel = self.compagnies_model.item(row, 2).text()
            
            # Validation finale
            if not compagnie:
                QMessageBox.warning(window, "Erreur", f"Le nom de la compagnie ne peut pas être vide (ligne {row+1})")
                return
            
            if zone not in ['A', 'B']:
                QMessageBox.warning(window, "Erreur", f"La zone doit être 'A' ou 'B' (ligne {row+1})")
                return
            
            if zone == 'A' and carrousel not in ['1', '2']:
                QMessageBox.warning(window, "Erreur", f"Pour la zone A, le carrousel doit être 1 ou 2 (ligne {row+1})")
                return
            
            if zone == 'B' and carrousel not in ['3', '4', '5']:
                QMessageBox.warning(window, "Erreur", f"Pour la zone B, le carrousel doit être 3, 4 ou 5 (ligne {row+1})")
                return
            
            compagnies.append((compagnie, zone, int(carrousel)))
        
        # Mettre à jour la base de données
        try:
            self.db.update_compagnies(compagnies)
            QMessageBox.information(window, "Succès", "Les modifications ont été enregistrées")
            window.close()
        except Exception as e:
            QMessageBox.critical(window, "Erreur", f"Une erreur est survenue : {str(e)}")

#-----------------------------------------------------------------------------------
    def optimise(self):
        # Récupérer les données de simulation
        sim_type = self.get_curent_simulation()
        result, data, sim = self.calcul_simulation(sim_type)
        
        # Créer une nouvelle fenêtre pour l'optimisation
        self.opt_window = QMainWindow()
        self.opt_window.setWindowTitle(f"Optimisation par Algorithme génétique -Affectation par Carrousels- Distribution {sim_type} ")
        self.opt_window.setGeometry(50, 50, 1000, 800)
        
        central_widget = QWidget()
        self.opt_window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        # type d'optimisation
        type_group = QGroupBox("optimisation ")
        type_layout = QHBoxLayout()

        type_Label_param=QLabel("Type:")
        type_Label_param.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        type_layout.addWidget(type_Label_param)
        self.type_optim_combo = QComboBox()
        self.type_optim_combo.addItems(["Compagnies", "Vols"])
        type_layout.addWidget(self.type_optim_combo)
        self.opt_type="Compagnies"

        type_group.setLayout(type_layout)
        main_layout.addWidget(type_group)
        
        # Paramètres d'optimisation
        params_group = QGroupBox("Paramètres")
        params_layout = QVBoxLayout()
        
        # Taille de population
        pop_layout = QHBoxLayout()
        population_Label_param=QLabel("Taille de population:")
        population_Label_param.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        pop_layout.addWidget(population_Label_param)
        self.pop_size_spin = QSpinBox()
        self.pop_size_spin.setRange(5, 100)
        self.pop_size_spin.setValue(20)#20
        pop_layout.addWidget(self.pop_size_spin)
        params_layout.addLayout(pop_layout)
        
        # Nombre de générations
        gen_layout = QHBoxLayout()
        nbgen_Label_param=QLabel("Nombre de générations:")
        nbgen_Label_param.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        gen_layout.addWidget(nbgen_Label_param)
        self.gen_spin = QSpinBox()
        self.gen_spin.setRange(5, 200)
        self.gen_spin.setValue(10)#30
        gen_layout.addWidget(self.gen_spin)
        params_layout.addLayout(gen_layout)
        
        # Taux de mutation
        mut_layout = QHBoxLayout()
        mut_Label_param=QLabel("Taux de mutation:")
        mut_Label_param.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        mut_layout.addWidget(mut_Label_param)
        self.mut_spin = QDoubleSpinBox()
        self.mut_spin.setRange(0.01, 1)
        self.mut_spin.setSingleStep(0.01)
        self.mut_spin.setValue(0.15)
        mut_layout.addWidget(self.mut_spin)
        params_layout.addLayout(mut_layout)
        

        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        main_layout.addWidget(self.progress_bar)
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton(self.icons['play'], "Démarrer")
        self.start_button.clicked.connect(self.start_optimisation)
        button_layout.addWidget(self.start_button)
        
        self.cancel_button = QPushButton(self.icons['stop'], "Annuler")
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Création du splitter pour diviser l'espace
        splitter = QSplitter(Qt.Vertical)
        
        # Zone de résultats textuels (1/3 de l'espace)
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        results_layout.addWidget(self.results_text)
        splitter.addWidget(results_container)
        
        # Zone de visualisation graphique (2/3 de l'espace)
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        
        # Contrôle de sélection du carrousel
        carrousel_control = QHBoxLayout()
        carrousel_control.addWidget(QLabel("Carrousel à visualiser:"))
        self.carrousel_combo = QComboBox()
        self.carrousel_combo.addItems(["Zone A-1", "Zone A-2", "Zone B-1", "Zone B-2", "Zone B-3"])
        carrousel_control.addWidget(self.carrousel_combo)
        self.optimization_export_button = QPushButton(self.icons['export'], "Exporter CSV")
        self.optimization_export_button.clicked.connect(self.optimization_export)
        carrousel_control.addWidget(self.optimization_export_button)
        graph_layout.addLayout(carrousel_control)
        
        # Graphique de comparaison
        self.comparison_fig = Figure(figsize=(10, 6))
        self.comparison_canvas = FigureCanvas(self.comparison_fig)
        graph_layout.addWidget(self.comparison_canvas)
        
        splitter.addWidget(graph_container)
        
        # Définir les proportions initiales
        splitter.setSizes([300, 500])  # 300 pour le texte, 500 pour le graphique
        
        main_layout.addWidget(splitter)
        
        # Stocker les données pour la comparaison
        self.initial_data = data
        self.optimized_data = None
        
        # Connecter le signal de changement de carrousel
        self.type_optim_combo.currentIndexChanged.connect(self.update_type_optim)
        self.carrousel_combo.currentIndexChanged.connect(self.update_comparison_graph)
        
        # Afficher la fenêtre
        self.opt_window.show()

    def update_type_optim(self):
        self.opt_type = self.type_optim_combo.currentText()

    def update_comparison_graph(self):
        """Met à jour le graphique de comparaison avec les données du carrousel sélectionné"""
        if not hasattr(self, 'initial_data') or not hasattr(self, 'optimized_data'):
            return
        
        carrousel_num = self.carrousel_combo.currentIndex() + 1
        carrousel_key = f"caroussel_{carrousel_num}"
        
        # Vérifier que les données existent
        if carrousel_key not in self.initial_data or (self.optimized_data and carrousel_key not in self.optimized_data):
            return
        
        # Effacer le graphique précédent
        self.comparison_fig.clear()
        ax = self.comparison_fig.add_subplot(111)
        
        # Récupérer les données initiales et optimisées
        initial = self.initial_data[carrousel_key]
        times = initial["times"]
        
        # Tracer les données initiales
        ax.plot(times, initial["Bagages_sur_tapis"], 'b-', label='Initial - Bagages sur tapis')
        ax.plot(times, initial["Bagages_rejetes"], 'b--', label='Initial - Bagages rejetés')
        
        # Tracer les données optimisées si disponibles
        if self.optimized_data:
            optimized = self.optimized_data[carrousel_key]
            ax.plot(times, optimized["Bagages_sur_tapis"], 'g-', label='Optimisé - Bagages sur tapis')
            ax.plot(times, optimized["Bagages_rejetes"], 'g--', label='Optimisé - Bagages rejetés')
        
        # Ajouter les lignes de capacité
        capacite_longueur = self.params.longueur_max / self.params.longueur_moyenne_bagage
        capacite_poids = self.params.poids_max / self.params.poids_moyen_bagage
        ax.axhline(y=capacite_longueur, color='orange', linestyle='--', label='Capacité max (longueur)')
        ax.axhline(y=capacite_poids, color='purple', linestyle='--', label='Capacité max (poids)')
        
        # Configurer le graphique
        ax.set_title(f"Comparaison avant/après optimisation - Carrousel {carrousel_num}")
        ax.set_ylabel("Nombre de bagages")
        ax.set_xlabel("Heure")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        # Simplifier les étiquettes d'axe x (juste les heures)
        simplified_times = []
        prev_hour = ""
        for t in times:
            hour = t.split(":")[0]
            if hour != prev_hour:
                simplified_times.append(f"{hour}h")
                prev_hour = hour
            else:
                simplified_times.append("")
        
        ax.set_xticks(range(len(times)))
        ax.set_xticklabels(simplified_times)
        
        # Rotation des étiquettes x pour plus de lisibilité
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.comparison_fig.tight_layout()
        self.comparison_canvas.draw()


    def start_optimisation(self):
        # Récupérer les paramètres
        self.opt_type = self.param_combo.currentText()
        optim_compagnies = self.opt_type == "Compagnies"
        max_carrousel = 5
        population_size = self.pop_size_spin.value()
        generations = self.gen_spin.value()
        mutation_rate = self.mut_spin.value()
       
        # Désactiver le bouton de démarrage
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
       
        # Lancer l'optimisation dans un thread séparé
        self.opt_thread = OptimizationThread(
                                                self,
                                                optim_compagnies,
                                                max_carrousel,
                                                population_size,
                                                generations,
                                                mutation_rate
                                            )
       
        self.opt_thread.progress_updated.connect(self.update_progress)
        self.opt_thread.results_ready.connect(self.show_optimization_results)
        self.opt_thread.finished.connect(self.optimization_finished)
        self.cancel_button.clicked.connect(self.opt_thread.terminate)
       
        self.opt_thread.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.results_text.append(message)

    def show_optimization_results(self, best_assignment,original_assignment, initial_failures, optimized_failures,data):
        self.results_text.append("\n=== Résultats de l'optimisation ===")
        self.results_text.append(f"Nombre d'échecs initial: {initial_failures}")
        self.results_text.append(f"Nombre d'échecs après optimisation: {optimized_failures}")
        
        self.results_text.append("\nMeilleure affectation trouvée:")
        for key, value in best_assignment.items():
            self.results_text.append(f"{key} ({original_assignment[key]}) -> Carrousel {value}")
        
        # Stocker les données optimisées et mettre à jour le graphique
        self.optimized_data  = data
        self.update_comparison_graph()

    def optimization_finished(self):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(100)

    def start_optimisation(self):
        # Récupérer les paramètres
        optim_compagnies = self.opt_type == "Compagnies"
        max_carrousel = 5
        population_size = self.pop_size_spin.value()
        generations = self.gen_spin.value()
        mutation_rate = self.mut_spin.value()
       
        # Désactiver le bouton de démarrage
        self.start_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
       
        # Lancer l'optimisation dans un thread séparé
        self.opt_thread = OptimizationThread(
            self,
            optim_compagnies,
            max_carrousel,
            population_size,
            generations,
            mutation_rate
           
        )
       
        self.opt_thread.progress_updated.connect(self.update_progress)
        self.opt_thread.results_ready.connect(self.show_optimization_results)
        self.opt_thread.finished.connect(self.optimization_finished)
        self.cancel_button.clicked.connect(self.opt_thread.terminate)
       
        self.opt_thread.start()

    def update_progress(self, value, message):
        self.progress_bar.setValue(value)
        self.results_text.append(message)



    def optimization_finished(self):
        self.start_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.progress_bar.setValue(100)

    def optimization_export(self):
        """Exporte les résultats de l'optimisation au format CSV"""
        if not hasattr(self, 'optimized_data'):
            QMessageBox.warning(self, "Export impossible", "Aucune donnée d'optimisation à exporter")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
                                                self, 
                                                "Exporter les résultats d'optimisation", 
                                                "", 
                                                "CSV Files (*.csv)"
                                            )
        
        if not filename:
            return
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire l'en-tête
                writer.writerow([
                                    'Heure',
                                    'Initial - Bagages sur tapis',
                                    'Initial - Poids sur tapis',
                                    'Initial - Longueur sur tapis',
                                    'Initial - Bagages rejetés',
                                    'Initial - Echec',
                                    'Optimisé - Bagages sur tapis',
                                    'Optimisé - Poids sur tapis',
                                    'Optimisé - Longueur sur tapis',
                                    'Optimisé - Bagages rejetés',
                                    'Optimisé - Echec'
                                ])
                
                # Écrire les données pour chaque carrousel
                for carrousel_num in range(1, 6):
                    writer.writerow([f"Carrousel {carrousel_num}"])
                    
                    initial_key = f"caroussel_{carrousel_num}"
                    optimized_key = f"caroussel_{carrousel_num}"
                    
                    times = self.initial_data[initial_key]['times']
                    initial_bags = self.initial_data[initial_key]['Bagages_sur_tapis']
                    initial_weight = self.initial_data[initial_key]['Poids_sur_tapis']
                    initial_length = self.initial_data[initial_key]['Longueur_sur_tapis']
                    initial_rejected = self.initial_data[initial_key]['Bagages_rejetes']
                    initial_failure = self.initial_data[initial_key]['Echec']
                    
                    optimized_bags = self.optimized_data[optimized_key]['Bagages_sur_tapis']
                    optimized_weight = self.optimized_data[optimized_key]['Poids_sur_tapis']
                    optimized_length = self.optimized_data[optimized_key]['Longueur_sur_tapis']
                    optimized_rejected = self.optimized_data[optimized_key]['Bagages_rejetes']
                    optimized_failure = self.optimized_data[optimized_key]['Echec']
                    
                    for i in range(len(times)):
                        writer.writerow([
                                            times[i],
                                            initial_bags[i],
                                            initial_weight[i],
                                            initial_length[i],
                                            initial_rejected[i],
                                            initial_failure[i],
                                            optimized_bags[i],
                                            optimized_weight[i],
                                            optimized_length[i],
                                            optimized_rejected[i],
                                            optimized_failure[i]
                                        ])
                    
                    writer.writerow([])  # Ligne vide entre les carrousels
                
            QMessageBox.information(self, "Export réussi", f"Les données ont été exportées dans {filename}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'export : {str(e)}")
#-----------------------------------------------------------------------------------
    def variation(self):
        sim_type = self.get_curent_simulation()
        
        # Créer une nouvelle fenêtre pour les variations
        self.var_window = QMainWindow()
        self.var_window.setWindowTitle(f"Variation des paramètres - {sim_type}")
        self.var_window.setGeometry(100, 100, 1000, 800)
        
        central_widget = QWidget()
        self.var_window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Paramètres de variation
        params_group = QGroupBox("Paramètres de variation")
        params_layout = QVBoxLayout()
        
        # Sélection du paramètre à faire varier
        param_layout = QHBoxLayout()
        val_param=QLabel("Paramètre à faire varier:")
        val_param.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        param_layout.addWidget(val_param)
        self.param_combo = QComboBox()
        
        # Remplir la combo box selon la distribution sélectionnée
        if sim_type == "normal":
            self.param_combo.addItems(["Écart-type (σ)"])
        elif sim_type == "poisson":
            self.param_combo.addItems(["Lambda (λ)"])
        elif sim_type == "binomialnegatif":
            self.param_combo.addItems(["Moyenne de la distribution (mu)", "Paramètre de dispersion (k)"])
        elif sim_type == "beta":
            self.param_combo.addItems(["Alpha (α)", "Beta (β)"])
        elif sim_type == "bimodal":
            self.param_combo.addItems([
                "Moyenne early", "Écart-type early", 
                "Moyenne late", "Écart-type late",
                "Poids early"
            ])
        elif sim_type == "lognormal":
            self.param_combo.addItems(["Mu (μ)", "Sigma (σ)"])
        elif sim_type == "gamma":
            self.param_combo.addItems(["Shape (k)", "Scale (θ)"])
        elif sim_type == "weibull":
            self.param_combo.addItems(["Shape (k)", "Scale (λ)"])
        elif sim_type == "trimodal":
            self.param_combo.addItems([
                "Moyenne pic 1", "Moyenne pic 2", "Moyenne pic 3",
                "Écart-type pic 1", "Écart-type pic 2", "Écart-type pic 3",
                "Poids pic 1", "Poids pic 2", "Poids pic 3"
            ])
        elif sim_type == "pareto":
            self.param_combo.addItems(["Alpha (α)", "Scale"])
        else:  # uniform
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Information)
            msg.setText(f"Aucun paramètre à faire varier pour la loi uniforme")
            msg.setWindowTitle("Variations")
            msg.exec_()
            return
        
        param_layout.addWidget(self.param_combo)
        params_layout.addLayout(param_layout)
        
        # Valeurs de variation
        range_layout = QHBoxLayout()
        
        val_min_label=QLabel("Valeur min:")
        val_min_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        range_layout.addWidget(val_min_label)
        self.val_min_spin = QDoubleSpinBox()
        self.val_min_spin.setRange(0, 1000)
        self.val_min_spin.setSingleStep(0.1)
        range_layout.addWidget(self.val_min_spin)
        
        val_max_label=QLabel("Valeur max:")
        val_max_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        range_layout.addWidget(val_max_label)
        self.val_max_spin = QDoubleSpinBox()
        self.val_max_spin.setRange(0, 1000)
        self.val_max_spin.setSingleStep(0.1)
        range_layout.addWidget(self.val_max_spin)
        
        val_step_label=QLabel("Pas:")
        val_step_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        range_layout.addWidget(val_step_label)
        self.val_step_spin = QDoubleSpinBox()
        self.val_step_spin.setRange(0.01, 10)
        self.val_step_spin.setSingleStep(0.01)
        self.val_step_spin.setValue(1)
        range_layout.addWidget(self.val_step_spin)
        
        params_layout.addLayout(range_layout)
        
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # Barre de progression
        self.var_progress_bar = QProgressBar()
        self.var_progress_bar.setRange(0, 100)
        main_layout.addWidget(self.var_progress_bar)
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        self.var_start_button = QPushButton(self.icons['play'], "Démarrer")
        self.var_start_button.clicked.connect(self.start_variation)
        button_layout.addWidget(self.var_start_button)
        
        self.var_cancel_button = QPushButton(self.icons['stop'], "Annuler")
        self.var_cancel_button.setEnabled(False)
        button_layout.addWidget(self.var_cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Création du splitter pour diviser l'espace
        splitter = QSplitter(Qt.Vertical)
        
        # Zone de résultats textuels (1/3 de l'espace)
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        self.var_results_text = QTextEdit()
        self.var_results_text.setReadOnly(True)
        results_layout.addWidget(self.var_results_text)
        splitter.addWidget(results_container)
        
        # Zone de visualisation graphique (2/3 de l'espace)
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)

         # Carrousel à analyser
        carrousel_layout = QHBoxLayout()
        val_var_combo_label=QLabel("Carrousel à analyser:")
        val_var_combo_label.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        carrousel_layout.addWidget(val_var_combo_label)
        self.carrousel_var_combo = QComboBox()
        self.carrousel_var_combo.addItems(["All","Zone A-1", "Zone A-2", "Zone B-1", "Zone B-2", "Zone B-3"])
        carrousel_layout.addWidget(self.carrousel_var_combo)

        self.variation_export_button = QPushButton(self.icons['export'], "Exporter CSV")
        self.variation_export_button.clicked.connect(self.variation_export)
        carrousel_layout.addWidget(self.variation_export_button)
        graph_layout.addLayout(carrousel_layout)
       
        # Graphique de variation
        self.var_fig = Figure(figsize=(10, 6))
        self.var_canvas = FigureCanvas(self.var_fig)
        graph_layout.addWidget(self.var_canvas)
        
        splitter.addWidget(graph_container)
        
        # Définir les proportions initiales
        splitter.setSizes([300, 500])  # 300 pour le texte, 500 pour le graphique
        
        main_layout.addWidget(splitter)
        
        # Afficher la fenêtre
        self.var_window.show()
        self.update_param_range()
        # Mettre à jour les valeurs min/max selon le paramètre sélectionné
        self.param_combo.currentTextChanged.connect(self.update_param_range)
        self.carrousel_var_combo.currentTextChanged.connect(self.show_variation_carrousel)

    def update_param_range(self):
        """Met à jour les valeurs min/max selon le paramètre sélectionné"""
        sim_type = self.get_curent_simulation()
        param = self.param_combo.currentText()
        
        # Définir des plages raisonnables selon le paramètre
        if "Écart-type" in param or "Sigma" in param:
            self.val_min_spin.setValue(5)
            self.val_max_spin.setValue(60)
            self.val_step_spin.setValue(5)
        elif "Lambda" in param:
            self.val_min_spin.setValue(0.01)
            self.val_max_spin.setValue(0.1)
            self.val_step_spin.setValue(0.01)
        elif "Alpha" in param or "Beta" in param:
            self.val_min_spin.setValue(0.1)
            self.val_max_spin.setValue(5)
            self.val_step_spin.setValue(0.1)
        elif "Moyenne" in param:
            if "early" in param.lower():
                self.val_min_spin.setValue(60)
                self.val_max_spin.setValue(180)
                self.val_step_spin.setValue(10)
            elif "late" in param.lower():
                self.val_min_spin.setValue(15)
                self.val_max_spin.setValue(60)
                self.val_step_spin.setValue(5)
            else:  # trimodal
                self.val_min_spin.setValue(15)
                self.val_max_spin.setValue(240)
                self.val_step_spin.setValue(15)
        elif "Poids" in param:
            self.val_min_spin.setValue(0.1)
            self.val_max_spin.setValue(0.9)
            self.val_step_spin.setValue(0.05)
        elif "Shape" in param:
            self.val_min_spin.setValue(0.1)
            self.val_max_spin.setValue(10)
            self.val_step_spin.setValue(0.1)
        elif "Scale" in param:
            self.val_min_spin.setValue(1)
            self.val_max_spin.setValue(100)
            self.val_step_spin.setValue(5)

    def start_variation(self):
        """Lance la simulation avec variation de paramètre"""
        sim_type = self.get_curent_simulation()
        param = self.param_combo.currentText()
        min_val = self.val_min_spin.value()
        max_val = self.val_max_spin.value()
        step = self.val_step_spin.value()

        
        # Désactiver le bouton de démarrage
        self.var_start_button.setEnabled(False)
        self.var_cancel_button.setEnabled(True)
        
        # Lancer la variation dans un thread séparé
        self.var_thread = VariationThread(
                                            self,
                                            sim_type,
                                            param,
                                            min_val,
                                            max_val,
                                            step
                                            )
        
        self.var_thread.progress_updated.connect(self.update_var_progress)
        self.var_thread.results_ready.connect(self.show_variation_results)
        self.var_thread.finished.connect(self.variation_finished)
        self.var_cancel_button.clicked.connect(self.var_thread.terminate)
        
        self.var_thread.start()

    def update_var_progress(self, value, message):
        """Met à jour la progression de la variation"""
        self.var_progress_bar.setValue(value)
        self.var_results_text.append(message)

    def show_variation_carrousel(self ):
        """Affiche les résultats de la variation"""
        carrousel_num = self.carrousel_var_combo.currentIndex() 
        if carrousel_num==0:
            titre=f"Tous les Carrousels"
        else:
            titre=f"Carrousel analysé: {carrousel_num}"
        failures=[failure[carrousel_num] for failure in self.variation_failures]

        # Afficher le graphique
        self.var_fig.clear()
        ax = self.var_fig.add_subplot(111)
        
        # Tracer les échecs 
        ax.plot(self.variation_values, failures, 'b-', label='Nombre d\'échecs')

        
        # Configurer le graphique
        ax.set_title(f"Impact du paramètre {self.param_combo.currentText()} /{titre} ")
        ax.set_xlabel(f"Valeur du paramètre {self.param_combo.currentText()}")
        ax.set_ylabel("Mesure d'impact")
        ax.grid(True, linestyle='--', alpha=0.7)
        ax.legend()
        
        self.var_fig.tight_layout()
        self.var_canvas.draw()

    def show_variation_results(self, param_values, failures ):
        """Affiche les résultats de la variation"""
        self.variation_values=param_values
        self.variation_failures=failures
        self.var_results_text.append("\n=== Résultats de la variation ===")
        self.var_results_text.append(f"Paramètre: {self.param_combo.currentText()}")
        self.show_variation_carrousel()


    def variation_finished(self):
        """Finalise l'interface après la variation"""
        self.var_start_button.setEnabled(True)
        self.var_cancel_button.setEnabled(False)
        self.var_progress_bar.setValue(100)

    def variation_export(self):
        """Exporte les résultats de la variation de paramètre au format CSV"""
        if not hasattr(self, 'variation_values') or not hasattr(self, 'variation_failures'):
            QMessageBox.warning(self, "Export impossible", "Aucune donnée de variation à exporter")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
                                                    self, 
                                                    "Exporter les résultats de variation", 
                                                    "", 
                                                    "CSV Files (*.csv)"
                                                )
        
        if not filename:
            return
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire l'en-tête
                writer.writerow([
                                    'Valeur paramètre',
                                    'Total échecs',
                                    'Carrousel 1 échecs',
                                    'Carrousel 2 échecs',
                                    'Carrousel 3 échecs', 
                                    'Carrousel 4 échecs',
                                    'Carrousel 5 échecs'
                                ])
                
                # Écrire les données
                for i in range(len(self.variation_values)):
                    row = [self.variation_values[i]]
                    row.extend(self.variation_failures[i])
                    writer.writerow(row)
                
                # Ajouter des métadonnées
                writer.writerow([])
                writer.writerow(['Paramètre varié:', self.param_combo.currentText()])
                writer.writerow(['Loi de distribution:', self.get_curent_simulation()])
                writer.writerow(['Valeur min:', self.val_min_spin.value()])
                writer.writerow(['Valeur max:', self.val_max_spin.value()])
                writer.writerow(['Pas:', self.val_step_spin.value()])
                
            QMessageBox.information(self, "Export réussi", f"Les données ont été exportées dans {filename}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'export : {str(e)}")
#-----------------------------------------------------------------------------------
    def simulation_periode(self):
        """Crée une fenêtre pour la simulation sur une période donnée"""
        # Créer une nouvelle fenêtre
        self.period_window = QMainWindow()
        self.period_window.setWindowTitle("Simulation par période")
        self.period_window.setGeometry(100, 100, 1000, 800)
        
        central_widget = QWidget()
        self.period_window.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Paramètres de période
        period_group = QGroupBox("Paramètres de période")
        period_layout = QHBoxLayout()
        
        # Date de début
        start_layout = QVBoxLayout()
        start_layout.addWidget(QLabel("Date de début:"))
        self.period_start_edit = QDateTimeEdit()
        self.period_start_edit.setDisplayFormat("dd/MM/yyyy")
        self.period_start_edit.setCalendarPopup(True)
        self.period_start_edit.setDate(QDate.currentDate())
        start_layout.addWidget(self.period_start_edit)
        period_layout.addLayout(start_layout)
        
        # Date de fin
        end_layout = QVBoxLayout()
        end_layout.addWidget(QLabel("Date de fin:"))
        self.period_end_edit = QDateTimeEdit()
        self.period_end_edit.setDisplayFormat("dd/MM/yyyy")
        self.period_end_edit.setCalendarPopup(True)
        self.period_end_edit.setDate(QDate.currentDate().addDays(7))  # Par défaut +7 jours
        end_layout.addWidget(self.period_end_edit)
        period_layout.addLayout(end_layout)
        
        # Bouton pour charger les données
        load_layout = QVBoxLayout()
        load_layout.addWidget(QLabel(""))
        load_button = QPushButton(self.icons['optimise'],"Charger les données")
        load_button.clicked.connect(self.load_period_data)
        load_layout.addWidget(load_button)
        period_layout.addLayout(load_layout)
        
        period_group.setLayout(period_layout)
        main_layout.addWidget(period_group)

        # Création du splitter pour diviser l'espace
        splitter = QSplitter(Qt.Vertical)
        
        # Zone de sélection des données (1/3 de l'espace)
        selection_container = QWidget()
        selection_layout = QHBoxLayout(selection_container)
        
        # Sélection des compagnies
        compagnie_group = QGroupBox("Compagnies disponibles")
        compagnie_layout = QVBoxLayout()
        self.period_compagnie_list = QListWidget()
        self.period_compagnie_list.setSelectionMode(QListWidget.MultiSelection)
        compagnie_layout.addWidget(self.period_compagnie_list)
        compagnie_group.setLayout(compagnie_layout)
        selection_layout.addWidget(compagnie_group)
        
        # Sélection des vols
        vol_group = QGroupBox("Vols disponibles")
        vol_layout = QVBoxLayout()
        self.period_vol_list = QListWidget()
        self.period_vol_list.setSelectionMode(QListWidget.MultiSelection)
        vol_layout.addWidget(self.period_vol_list)
        vol_group.setLayout(vol_layout)
        selection_layout.addWidget(vol_group)
        
        splitter.addWidget(selection_container)
        
        # Barre de progression
        self.period_progress = QProgressBar()
        self.period_progress.setRange(0, 100)
        main_layout.addWidget(self.period_progress)
        
        # Boutons de contrôle
        button_layout = QHBoxLayout()
        
        self.period_start_button = QPushButton(self.icons['play'], "Démarrer")
        self.period_start_button.clicked.connect(self.start_simulation_periode)
        button_layout.addWidget(self.period_start_button)
        
        self.period_cancel_button = QPushButton(self.icons['stop'], "Annuler")
        self.period_cancel_button.clicked.connect(self.stop_simulation_periode)
        self.period_cancel_button.setEnabled(False)
        button_layout.addWidget(self.period_cancel_button)
        
        main_layout.addLayout(button_layout)
        
        # Zone de texte pour les logs
        self.period_log = QTextEdit()
        self.period_log.setReadOnly(True)
        main_layout.addWidget(self.period_log)
        

        # Zone de visualisation (2/3 de l'espace)
        graph_container = QWidget()
        graph_layout = QVBoxLayout(graph_container)
        
        # Contrôles du graphique
        graph_control = QHBoxLayout()
        label_type=QLabel("Type de données:")
        label_type.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        graph_control.addWidget(label_type)
        self.period_data_combo = QComboBox()
        self.period_data_combo.addItems(["Bagages", "Vols", "Voyageurs","All Carrousels","Carrousel-Zone A-1", "Carrousel-Zone A-2", "Carrousel-Zone B-1", "Carrousel-Zone B-2", "Carrousel-Zone B-3"])
        graph_control.addWidget(self.period_data_combo)
        self.period_export_button = QPushButton(self.icons['export'], "Exporter CSV")
        self.period_export_button.clicked.connect(self.start_simulation_periode_export)
        graph_control.addWidget(self.period_export_button)
        graph_layout.addLayout(graph_control)
        
        # Connecter les signaux de changement
        self.period_data_combo.currentIndexChanged.connect(self.update_periode_graph)

        
        # Graphique
        self.period_fig = Figure(figsize=(10, 6))
        self.period_canvas = FigureCanvas(self.period_fig)
        graph_layout.addWidget(self.period_canvas)
        
        splitter.addWidget(graph_container)
        
        # Définir les proportions initiales
        splitter.setSizes([300, 500])
        main_layout.addWidget(splitter)
        
        # Stockage des données chargées
        self.period_data = None
        self.period_compagnies = []
        self.period_vols = []
        self.period_results = {}
        
        # Afficher la fenêtre
        self.period_window.show()

    def load_period_data(self):
        """Charge les données pour la période sélectionnée"""
        start_date = self.period_start_edit.date().toString("yyyy-MM-dd")
        end_date = self.period_end_edit.date().toString("yyyy-MM-dd")
        site = self.site_combo.currentText()
        self.period_compagnie_list.clear()
        self.period_vol_list.clear()
        self.period_log.append(f"Chargement des données du {start_date} au {end_date}...")
        self.period_progress.setValue(10)
        
        # Récupérer les compagnies sur la période
        self.period_compagnies = self.db.get_compagnies_period(site, start_date, end_date)

        self.period_compagnie_list.addItems(self.period_compagnies)
        
        self.period_progress.setValue(50)
        self.period_log.append(f"{len(self.period_compagnies)} compagnies trouvées")
        
        # Connecter le signal de sélection des compagnies
        self.period_compagnie_list.itemSelectionChanged.connect(self.update_period_vols)
        
        self.period_progress.setValue(100)
        self.period_log.append("Chargement terminé")

    def update_period_vols(self):
        """Met à jour la liste des vols en fonction des compagnies sélectionnées"""
        selected_compagnies = [item.text() for item in self.period_compagnie_list.selectedItems()]
        if not selected_compagnies:
            return
        
        start_date = self.period_start_edit.date().toString("yyyy-MM-dd")
        end_date = self.period_end_edit.date().toString("yyyy-MM-dd")
        site = self.site_combo.currentText()
        
        self.period_log.append(f"Chargement des vols pour {len(selected_compagnies)} compagnies...")
        self.period_progress.setValue(0)
        
        # Récupérer les vols pour les compagnies sélectionnées
        self.period_vols = []
        for compagnie in selected_compagnies:
            vols = self.db.get_vols_period(site, start_date, end_date, compagnie)
            self.period_vols.extend(vols)
        
        self.period_vol_list.clear()
        self.period_vol_list.addItems(self.period_vols)
        
        self.period_progress.setValue(100)
        self.period_log.append(f"{len(self.period_vols)} vols trouvés")

    def start_simulation_periode(self):
        """Démarre la simulation sur la période sélectionnée"""
        selected_vols = [item.text() for item in self.period_vol_list.selectedItems()]
        selected_compagnies = [item.text() for item in self.period_compagnie_list.selectedItems()]
        
        start_date = self.period_start_edit.date()
        end_date = self.period_end_edit.date()
        sim_type = self.get_curent_simulation()
        
        self.period_start_button.setEnabled(False)
        self.period_cancel_button.setEnabled(True)
        self.period_results = {}
        
        # Créer un thread pour la simulation
        self.update_params()
        self.period_thread = PeriodSimulationThread(
            self,
            sim_type,
            selected_compagnies,
            selected_vols,
            start_date,
            end_date
        )
        
        self.period_thread.progress_updated.connect(self.update_period_progress)
        self.period_thread.results_ready.connect(self.store_period_results)
        self.period_thread.finished.connect(self.period_simulation_finished)
        
        self.period_thread.start()

    def stop_simulation_periode(self):
        """Arrête la simulation en cours"""
        if hasattr(self, 'period_thread') and self.period_thread.isRunning():
            self.period_thread.terminate()
            self.period_log.append("Simulation arrêtée par l'utilisateur")
        
        self.period_start_button.setEnabled(True)
        self.period_cancel_button.setEnabled(False)

    def update_period_progress(self, progress, message):
        """Met à jour la progression de la simulation"""
        self.period_progress.setValue(progress)
        self.period_log.append(message)

    def store_period_results(self,  results):
        """Stocke les résultats d'une journée de simulation"""
        self.period_results = results
        self.update_periode_graph()

    def period_simulation_finished(self):
        """Finalise l'interface après la simulation"""
        self.period_start_button.setEnabled(True)
        self.period_cancel_button.setEnabled(False)
        self.period_progress.setValue(100)
        self.period_log.append("Simulation terminée")

    def update_periode_graph(self):
        """Met à jour le graphique avec les résultats de la simulation"""
        if not self.period_results:
            return
        
        data_typeIdx = self.period_data_combo.currentIndex()
        data_type = self.period_data_combo.currentText()
        
        self.period_fig.clear()
        ax = self.period_fig.add_subplot(111)
        
        dates = sorted(self.period_results.keys())
        values = []
        
        for date in dates:
            results = self.period_results[date]
            
            if data_typeIdx ==0:
                data = results["bagages"]
            elif data_typeIdx == 1:
                data = results["vols"]
            elif data_typeIdx == 2:
                data = results["voyageurs"]
            elif data_typeIdx == 3:
                data = results["nombre_echec"]
            else:  # Carrousel
                carrousel_num = data_typeIdx-3
                data = results[f"{carrousel_num}"]
            values.append(data)
        
        # Tracer le graphique
        ax.bar(dates, values)
        ax.set_title(f"{data_type} ")
        #ax.set_xlabel("Date")
        ax.set_ylabel("Nombre" if data_typeIdx <= 2 else "Echec")
        ax.grid(True, linestyle='--', alpha=0.7)
        
        # Rotation des dates pour meilleure lisibilité
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
        
        self.period_fig.tight_layout()
        self.period_canvas.draw()

    def start_simulation_periode_export(self):
        """Exporte les résultats de la simulation par période au format CSV"""
        if not self.period_results:
            QMessageBox.warning(self, "Export impossible", "Aucune donnée de simulation à exporter")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
                                                    self,
                                                    "Exporter les résultats de simulation",
                                                    "",
                                                    "CSV Files (*.csv)"
                                                )
        
        if not filename:
            return
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire l'en-tête
                writer.writerow([
                                    'Date',
                                    'Nombre de bagages',
                                    'Nombre de vols',
                                    'Nombre de voyageurs',
                                    'Nombre total d\'échecs',
                                    'Échecs Carrousel 1',
                                    'Échecs Carrousel 2',
                                    'Échecs Carrousel 3',
                                    'Échecs Carrousel 4',
                                    'Échecs Carrousel 5'
                                ])
                
                # Écrire les données pour chaque date
                for date, results in sorted(self.period_results.items()):
                    writer.writerow([
                                        date,
                                        results['bagages'],
                                        results['vols'],
                                        results['voyageurs'],
                                        results['nombre_echec'],
                                        results['1'],  # Échecs Carrousel 1
                                        results['2'],  # Échecs Carrousel 2
                                        results['3'],  # Échecs Carrousel 3
                                        results['4'],  # Échecs Carrousel 4
                                        results['5']   # Échecs Carrousel 5
                                    ])
                
                # Ajouter des métadonnées
                writer.writerow([])
                writer.writerow(['Paramètres de simulation:'])
                writer.writerow(['Type de distribution:', self.get_curent_simulation()])
                writer.writerow(['Date de début:', self.period_start_edit.date().toString("yyyy-MM-dd")])
                writer.writerow(['Date de fin:', self.period_end_edit.date().toString("yyyy-MM-dd")])
                writer.writerow(['Site:', self.site_combo.currentText()])
                writer.writerow(['Compagnies:', ', '.join([item.text() for item in self.period_compagnie_list.selectedItems()])])
                writer.writerow(['Vols:', ', '.join([item.text() for item in self.period_vol_list.selectedItems()])])
            
            QMessageBox.information(self, "Export réussi", f"Les données ont été exportées dans {filename}")
        
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'export : {str(e)}")
#-----------------------------------------------------------------------------------
    def optimise_traitement(self):
        """Optimise UN SEUL paramètre de traitement choisi par l'utilisateur."""
        self.opt_traitement_window = QMainWindow()
        self.opt_traitement_window.setWindowTitle("Optimisation ciblée des paramètres de traitement")
        self.opt_traitement_window.setGeometry(100, 100, 800, 600)
        
        central_widget = QWidget()
        self.opt_traitement_window.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 1. Sélection du paramètre à optimiser
        param_group = QGroupBox("Paramètre à optimiser")
        param_layout = QVBoxLayout()
        
        self.param_combo = QComboBox()
        self.param_combo.addItems([
                                    "Débit de traitement (bagages/min)", 
                                    "Poids max du tapis (kg)", 
                                    "Longueur max du tapis (m)"
                                  ])
        self.param_combo.currentTextChanged.connect(self.parametres_optimise_traitement)
        param_layout.addWidget(self.param_combo)
        param_group.setLayout(param_layout)
        layout.addWidget(param_group)

        # 2. Plage de variation
        range_group = QGroupBox("Plage de variation")
        range_layout = QHBoxLayout()

        label_min=QLabel("Valeur min:")
        label_min.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        range_layout.addWidget(label_min)
        self.min_spin = QDoubleSpinBox()
        self.min_spin.setRange(0, 9999)
        range_layout.addWidget(self.min_spin)
        
        label_max=QLabel("Valeur max:")
        label_max.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        range_layout.addWidget(label_max)
        self.max_spin = QDoubleSpinBox()
        self.max_spin.setRange(0, 9999)
        range_layout.addWidget(self.max_spin)
        
        label_step=QLabel("Pas:")
        label_step.setAlignment(Qt.AlignRight|Qt.AlignVCenter)
        range_layout.addWidget(label_step)
        self.step_spin = QDoubleSpinBox()
        self.step_spin.setRange(0.1, 100)
        self.step_spin.setValue(1)
        range_layout.addWidget( self.step_spin)
        
        range_group.setLayout(range_layout)
        layout.addWidget(range_group)

         
        
        # Barre de progression
        self.period_progress = QProgressBar()
        self.period_progress.setRange(0, 100)
        layout.addWidget(self.period_progress)

        # 3. Contrôles
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton(self.icons['play'], "Lancer l'optimisation")
        self.start_btn.clicked.connect(self.launch_param_optimisation)
        control_layout.addWidget(self.start_btn)
        
        self.cancel_btn = QPushButton(self.icons['stop'], "Annuler")
        self.cancel_btn.setEnabled(False)
        control_layout.addWidget(self.cancel_btn)
        layout.addLayout(control_layout)

        # Zone de texte pour les logs
        self.period_log = QTextEdit()
        self.period_log.setReadOnly(True)
        layout.addWidget(self.period_log)

        # 4. Carrousel à analyser
        carrousel_group = QGroupBox("Zone d'analyse")
        carrousel_layout = QHBoxLayout()
        
        self.carrousel_combo = QComboBox()
        self.carrousel_combo.addItems(["Tous", "Zone A-1", "Zone A-2", "Zone B-1", "Zone B-2", "Zone B-3"])
        self.carrousel_combo.currentTextChanged.connect(self.draw_optimise_traitement)
        carrousel_layout.addWidget(self.carrousel_combo)
        self.optimise_traitement_button = QPushButton(self.icons['export'], "Exporter CSV")
        self.optimise_traitement_button.clicked.connect(self.optimise_traitement_export)
        carrousel_layout.addWidget(self.optimise_traitement_button)
        carrousel_group.setLayout(carrousel_layout)
        layout.addWidget(carrousel_group)

        # 5. Résultats
        self.results_table = QTableView()
        self.results_model = QStandardItemModel()
        self.results_model.setHorizontalHeaderLabels(["Valeur testée", "Échecs totaux", "Taux de saturation (%)"])
        self.results_table.setModel(self.results_model)
        layout.addWidget(self.results_table)

        # 6. Graphique
        self.plot_fig = Figure()
        self.plot_canvas = FigureCanvas(self.plot_fig)
        layout.addWidget(self.plot_canvas)
        self.parametres_optimise_traitement()
        self.opt_traitement_window.show()
        self.optimise_traitement_results=None

    def  parametres_optimise_traitement(self):
        param_idx = self.param_combo.currentIndex()
        if param_idx == 0:
            self.min_spin.setValue(1)
            self.max_spin.setValue(6)
            self.step_spin.setValue(1)
        elif param_idx == 1:
            self.min_spin.setValue(1700)
            self.max_spin.setValue(3000)
            self.step_spin.setValue(100)
        elif param_idx == 2:
            self.min_spin.setValue(64)
            self.max_spin.setValue(100)
            self.step_spin.setValue(1)


    def draw_optimise_traitement(self):
        """Affiche les résultats sous forme de tableau et de courbe."""
        if not self.optimise_traitement_results:
            return
        results=self.optimise_traitement_results
        carrousel_idx = self.carrousel_combo.currentIndex()
        self.results_model.clear()
        self.results_model.setHorizontalHeaderLabels(["Valeur testée", "Échecs totaux", "Taux de saturation (%)"])
        
        x_vals, y_vals = [], []
        for key, valeur in results.items():
            failures=valeur[0][carrousel_idx]
            saturation=valeur[1][carrousel_idx]
            self.results_model.appendRow([
                                        QStandardItem(f"{key:.2f}"),
                                        QStandardItem(str(failures)),
                                        QStandardItem(f"{saturation:.1f}%")
                                    ])
            x_vals.append(key)
            y_vals.append(saturation)
        
        # Tracer la courbe
        self.plot_fig.clear()
        ax = self.plot_fig.add_subplot(111)
        ax.plot(x_vals, y_vals, 'b-')
        ax.set_xlabel(self.param_combo.currentText())
        ax.set_ylabel("Taux de saturation (%)")
        ax.grid(True)
        self.plot_canvas.draw()

    def launch_param_optimisation(self):
        """Lance l'optimisation sur le paramètre sélectionné."""
        param_idx = self.param_combo.currentIndex()
        param_name = ["traitement", "poids_max", "longueur_max"][param_idx]
        
        # Configurer le thread d'optimisation
        self.opt_thread = SingleParamOptimisationThread(
                                                            app=self,
                                                            param_name=param_name,
                                                            min_val=self.min_spin.value(),
                                                            max_val=self.max_spin.value(),
                                                            step=self.step_spin.value()
        )
        
        self.opt_thread.finished.connect(self.period_optimisation_finished)
        self.opt_thread.progress_updated.connect(self.update_optimisation_progress)
        self.opt_thread.results_ready.connect(self.display_optimisation_results)
        self.opt_thread.start()
        
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.cancel_btn.clicked.connect(self.opt_thread.terminate)

    def update_optimisation_progress(self, progress, message):
        """Met à jour la progression de la simulation"""
        self.period_progress.setValue(progress)
        self.period_log.append(message)
        
    def display_optimisation_results(self, results):
        """Affiche les résultats sous forme de tableau et de courbe."""
        self.optimise_traitement_results=results
        self.draw_optimise_traitement()

    def period_optimisation_finished(self):
        """Finalise l'interface après la simulation"""
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.period_progress.setValue(100)
        self.period_log.append("Simulation terminée")
        
    def optimise_traitement_export(self):
        """Exporte les résultats de l'optimisation des paramètres de traitement au format CSV"""
        if not hasattr(self, 'optimise_traitement_results') or not self.optimise_traitement_results:
            QMessageBox.warning(self.opt_traitement_window, "Export impossible", "Aucune donnée d'optimisation à exporter")
            return
        
        filename, _ = QFileDialog.getSaveFileName(
                                                    self.opt_traitement_window,
                                                    "Exporter les résultats d'optimisation",
                                                    "",
                                                    "CSV Files (*.csv)"
                                                )
        
        if not filename:
            return
        
        if not filename.endswith('.csv'):
            filename += '.csv'
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';')
                
                # Écrire l'en-tête
                writer.writerow([
                                    'Valeur paramètre',
                                    'Échecs totaux',
                                    'Échecs Zone A-1',
                                    'Échecs Zone A-2',
                                    'Échecs Zone B-1',
                                    'Échecs Zone B-2',
                                    'Échecs Zone B-3',
                                    'Taux saturation total (%)',
                                    'Taux saturation Zone A-1 (%)',
                                    'Taux saturation Zone A-2 (%)',
                                    'Taux saturation Zone B-1 (%)',
                                    'Taux saturation Zone B-2 (%)',
                                    'Taux saturation Zone B-3 (%)'
                                ])
                
                # Écrire les données pour chaque valeur testée
                for param_value, (failures, saturations) in sorted(self.optimise_traitement_results.items()):
                    writer.writerow([
                                        param_value,
                                        failures[0],  # Total
                                        failures[1],  # Zone A-1
                                        failures[2],  # Zone A-2
                                        failures[3],  # Zone B-1
                                        failures[4],  # Zone B-2
                                        failures[5],  # Zone B-3
                                        saturations[0],  # Total
                                        saturations[1],  # Zone A-1
                                        saturations[2],  # Zone A-2
                                        saturations[3],  # Zone B-1
                                        saturations[4],  # Zone B-2
                                        saturations[5]   # Zone B-3
                                    ])
                
                # Ajouter des métadonnées
                writer.writerow([])
                writer.writerow(['Paramètres de simulation:'])
                writer.writerow(['Type de distribution:', self.get_curent_simulation()])
                writer.writerow(['Paramètre optimisé:', self.param_combo.currentText()])
                writer.writerow(['Valeur min:', self.min_spin.value()])
                writer.writerow(['Valeur max:', self.max_spin.value()])
                writer.writerow(['Pas:', self.step_spin.value()])
                writer.writerow(['Date:', QDate.currentDate().toString("yyyy-MM-dd")])
            
            QMessageBox.information(
                self.opt_traitement_window,
                "Export réussi",
                f"Les données ont été exportées dans {filename}"
            )
        
        except Exception as e:
            QMessageBox.critical(
                self.opt_traitement_window,
                "Erreur",
                f"Une erreur est survenue lors de l'export : {str(e)}"
            )
#-----------------------------------------------------------------------------------
    def optimise_duree(self):
        pass
#-----------------------------------------------------------------------------------
class OptimizationThread(QThread):
    progress_updated = pyqtSignal(int, str)
    results_ready = pyqtSignal(dict,dict, int, int,dict)
   
    def __init__(self, app, optim_compagnies, max_carrousel, population_size, generations, mutation_rate):
        super().__init__()
        self.app = app
        self.optim_compagnies = optim_compagnies
        self.max_carrousel = max_carrousel
        self.population_size = population_size
        self.generations = generations
        self.mutation_rate = mutation_rate
        self._is_running = True
   
    def run(self):
        # Créer une copie de la simulation actuelle
        sim_type = self.app.get_curent_simulation()
        result, data ,sim = self.app.calcul_simulation(sim_type)
                 
       
        # Évaluation initiale
        initial_failures = data["nombre_echec"]
        self.progress_updated.emit(0, f"Évaluation initiale: {initial_failures} échecs")
       

        # Créer l'optimiseur

        optimiseur = OptimiseurGP(
                            sim,
                            max_carrousel=self.max_carrousel,
                            optim_compagnies=self.optim_compagnies,
                            population_size=self.population_size,
                            generations=self.generations,
                            mutation_rate=self.mutation_rate
                                )

        # Connecter le signal de progression
        optimiseur.progress_updated.connect(self.handle_progress_update)
        
        # Lancer l'optimisation
        best_assignment,optimized_failures,original_liste = optimiseur.run()

        # Évaluation finale
        if self.optim_compagnies:
            sim.init_db_compagnies(best_assignment)
        else:
            sim.init_db_flights(best_assignment)
       
        # Évaluation finale
        data = sim.run()
        result = sim.simulate(data)
        optimized_failures = result["nombre_echec"]
       
        self.results_ready.emit(best_assignment,original_liste, initial_failures, optimized_failures,result)
    
   
    def handle_progress_update(self, progress, message):
        """Transmet la progression à l'interface"""
        self.progress_updated.emit(progress, message)
   
    def terminate(self):
        self._is_running = False
        super().terminate()
#-----------------------------------------------------------------------------------
class VariationThread(QThread):
    progress_updated = pyqtSignal(int, str)
    results_ready = pyqtSignal(list, list)
    
    def __init__(self, app, sim_type, param, min_val, max_val, step):
        super().__init__()
        self.app = app
        self.sim_type = sim_type
        self.param = param
        self.min_val = min_val
        self.max_val = max_val
        self.step = step
        self._is_running = True
    
    def run(self):
        param_values = []
        failures = []

        
        # Calculer le nombre total d'étapes
        num_steps = int((self.max_val - self.min_val) / self.step) + 1
        current_step = 0

        # Parcourir les valeurs du paramètre
        val = self.min_val
        while val <= self.max_val and self._is_running:
            # Mettre à jour la progression
            progress = int((current_step / num_steps) * 100)
            self.progress_updated.emit(progress, f"Simulation avec {self.param} = {val:.2f}")
            
            # Créer une nouvelle simulation avec le paramètre modifié
            result, data, sim = self.run_simulation_with_param(val)

            # Calculer le temps total de saturation (en minutes)
            failure=[data["nombre_echec"],0,0,0,0,0]
            for i in range(1, 6):
                failure[i] = data[f"caroussel_{i}"]["nombre_echec"] 
            # Stocker les résultats
            param_values.append(val)
            failures.append(failure)

            val += self.step
            current_step += 1
        
        # Émettre les résultats finaux
        if self._is_running:
            self.results_ready.emit(param_values, failures)
    
    def run_simulation_with_param(self, param_value):
        """Exécute une simulation avec la valeur du paramètre spécifiée"""
        self.app.update_params()

        if self.sim_type == "normal" and "Écart-type" in self.param:
            sim = Simulate_normale(self.app.params, sigma_minutes=int(param_value))
        elif self.sim_type == "poisson" and "Lambda" in self.param:
            sim = Simulate_poisson(self.app.params, lambda_param=param_value)
        elif self.sim_type == "beta":
            if "Alpha" in self.param:
                sim = Simulate_beta(self.app.params, alpha=param_value, beta=self.app.beta_spin.value())
            else:
                sim = Simulate_beta(self.app.params, alpha=self.app.alpha_spin.value(), beta=param_value)
        elif self.sim_type == "binomialnegatif":
            if "mu" in self.param:
                sim = Simulate_binomialnegatif(self.app.params, mu=param_value, k=self.app.k_spin.value())
            else:
                sim = Simulate_binomialnegatif(self.app.params, mu=self.app.mu_spin.value(), k=param_value)
        elif self.sim_type == "bimodal":
            if "Moyenne early" in self.param:
                sim = Simulate_bimodal(
                    self.app.params,
                    early_mean=param_value,
                    early_std=self.app.early_std_spin.value(),
                    late_mean=self.app.late_mean_spin.value(),
                    late_std=self.app.late_std_spin.value(),
                    early_weight=self.app.early_weight_slider.value() / 100
                )
            elif "Écart-type early" in self.param:
                sim = Simulate_bimodal(
                    self.app.params,
                    early_mean=self.app.early_mean_spin.value(),
                    early_std=param_value,
                    late_mean=self.app.late_mean_spin.value(),
                    late_std=self.app.late_std_spin.value(),
                    early_weight=self.app.early_weight_slider.value() / 100
                )
            elif "Moyenne late" in self.param:
                sim = Simulate_bimodal(
                    self.app.params,
                    early_mean=self.app.early_mean_spin.value(),
                    early_std=self.app.early_std_spin.value(),
                    late_mean=param_value,
                    late_std=self.app.late_std_spin.value(),
                    early_weight=self.app.early_weight_slider.value() / 100
                )
            elif "Écart-type late" in self.param:
                sim = Simulate_bimodal(
                    self.app.params,
                    early_mean=self.app.early_mean_spin.value(),
                    early_std=self.app.early_std_spin.value(),
                    late_mean=self.app.late_mean_spin.value(),
                    late_std=param_value,
                    early_weight=self.app.early_weight_slider.value() / 100
                )
            elif "Poids early" in self.param:
                sim = Simulate_bimodal(
                    self.app.params,
                    early_mean=self.app.early_mean_spin.value(),
                    early_std=self.app.early_std_spin.value(),
                    late_mean=self.app.late_mean_spin.value(),
                    late_std=self.app.late_std_spin.value(),
                    early_weight=param_value
                )

        
        result = sim.run()
        data = sim.simulate(result)
        return result, data, sim
    
    def terminate(self):
        self._is_running = False
        super().terminate()
#-----------------------------------------------------------------------------------
class PeriodSimulationThread(QThread):
    progress_updated = pyqtSignal(int, str)
    results_ready = pyqtSignal( dict)
    
    def __init__(self, app, sim_type,compagnies,vols, start_date, end_date):
        super().__init__()
        self.app = app
        self.sim_type = sim_type
        self.params = deepcopy(app.params)
        self.params.compagnies = compagnies
        self.params.num_vols = vols
        self.start_date = start_date
        self.end_date = end_date
        self._is_running = True
    
    def run(self):
        current_date = self.start_date
        total_days = self.start_date.daysTo(self.end_date) + 1
        current_day = 0
        daily_results={}
        while current_date <= self.end_date and self._is_running:
            date_str = current_date.toString("yyyy-MM-dd")
            self.progress_updated.emit(int((current_day / total_days) * 100),f"Simulation pour {date_str}...")
            
            # Configurer les paramètres pour cette date
            self.params.date_str = date_str
            
            # Exécuter la simulation
            result, data, sim = self.app.calcul_simulation(self.sim_type,self.params)
         
            # Préparer les résultats pour cette journée
            daily_result = {
                "bagages": sum([sum([bag[1] for bag in bagage])   for bagage in result["bagages"]]),
                "vols": sum(len(vol)  for vol in result["vols"]),
                "voyageurs": sum(len(voyageur)  for voyageur in result["voyageurs"]),
                "nombre_echec": data["nombre_echec"]
            }

            # Ajouter les données des carrousels
            for i in range(1, 6):
                daily_result[f"{i}"] = data[f"caroussel_{i}"]["nombre_echec"]

            current_date = current_date.addDays(1)
            current_day += 1
            daily_results[date_str]=daily_result
        # Émettre les résultats
        self.results_ready.emit( daily_results)
    
    def terminate(self):
        self._is_running = False
        super().terminate()
#-----------------------------------------------------------------------------------
# Classes déléguées pour la validation des données
class ZoneDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        editor.addItems(['A', 'B'])
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setCurrentText(value)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)

class CarrouselDelegate(QStyledItemDelegate):
    def createEditor(self, parent, option, index):
        editor = QComboBox(parent)
        
        # Déterminer la zone pour cette ligne
        zone_index = index.model().index(index.row(), 1)
        zone = index.model().data(zone_index, Qt.DisplayRole)
        
        if zone == 'A':
            editor.addItems(['1', '2'])
        else:
            editor.addItems(['3', '4', '5'])
        
        return editor
    
    def setEditorData(self, editor, index):
        value = index.model().data(index, Qt.DisplayRole)
        editor.setCurrentText(value)
    
    def setModelData(self, editor, model, index):
        model.setData(index, editor.currentText(), Qt.EditRole)
#-----------------------------------------------------------------------------------
class SingleParamOptimisationThread(QThread):
    progress_updated = pyqtSignal(int, str)
    results_ready = pyqtSignal(dict)

    def __init__(self, app, param_name, min_val, max_val, step):
        super().__init__()
        self.app = app
        self.sim_type=self.app.get_curent_simulation()
        self.params = deepcopy(app.params)
        self.param_name = param_name  # "traitement"|"poids_max"|"longueur_max"
        self.min_val = min_val
        self.max_val = max_val
        self.step = step


    def run(self):
        results = {}
        current_val = self.min_val
        step_count = int((self.max_val - self.min_val) / self.step) + 1

        for i in range(step_count):
            if current_val > self.max_val:
                break
                
            # Mettre à jour le paramètre
            setattr(self.params, self.param_name, int(current_val))
            
            result, data, sim = self.app.calcul_simulation(self.sim_type,self.params)
            len_data_times=len(result["times"])

            daily_echec={}
            daily_echec[0]=data["nombre_echec"]
            # Ajouter les données des carrousels
            for j in range(1, 6):
                daily_echec[j] = sum([x for x in data[f"caroussel_{j}"]["Echec"]])
            
            daily_saturation={}
            saturation = (data["nombre_echec"] / len_data_times) * 20
            daily_saturation[0]= saturation
            for j in range(1, 6):
                daily_saturation[j] = (daily_echec[j] / len_data_times) * 100


            results[current_val]=[daily_echec,daily_saturation]
            
            # Mettre à jour la progression
            progress = int(i  * (100/step_count))
            self.progress_updated.emit(
                                        progress,
                                        f"{self.param_name}={current_val:.2f} → {saturation:.1f}% saturation"
                                    )
            
            current_val += self.step
        
        self.results_ready.emit(results)
#-----------------------------------------------------------------------------------
if __name__ == "__main__":
    logging.getLogger("PyQt5").setLevel(logging.CRITICAL)  # ou logging.ERROR
    app = QApplication(sys.argv)
    screen = app.primaryScreen()
    window = SimulationApp()
    window.resize(screen.size().width(), screen.size().height()-40)
    window.show()
    sys.exit(app.exec_())