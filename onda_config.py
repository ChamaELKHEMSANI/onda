import json

class Params:
    def __init__(self, config_file="config.json"):
        with open(config_file, 'r',encoding='utf-8') as f:
            self.config = json.load(f)
        
        # Paramètres de base
        self.db_path = self.get_config("db_path", expected_type=str)
        self.site = self.get_config("default_site", expected_type=str)
        self.date_str = self.get_config("default_date", expected_type=str)
        self.default_seed = self.get_config("default_seed", default=10, expected_type=int)

        # Paramètres temporels
        self.day_start = self.get_config("default_day_start", expected_type=str)
        self.day_end = self.get_config("default_day_end", expected_type=str)
        self.step_time = self.get_config("default_step_time", expected_type=int)
        self.open_min = self.get_config("default_open_min", expected_type=int)
        self.close_min = self.get_config("default_close_min", expected_type=int)
        self.compagnies = self.get_config("default_compagnie", default=[], expected_type=str)
        self.num_vols = self.get_config("default_num_vol", default=[], expected_type=str)

        # Paramètres bagages
        self.max_bagage = self.get_config("baggage.max_per_passenger", default=3, expected_type=int)
        self.poids_moyen_bagage = self.get_config("baggage.average_weight", default=25, expected_type=int)
        self.longueur_moyenne_bagage = self.get_config("baggage.average_length", default=0.8, expected_type=float)
        
        # Paramètres convoyeur
        self.traitement = self.get_config("conveyor.average_processing_rate", default=2, expected_type=int)
        self.poids_max = self.get_config("conveyor.max_weight", default=1200, expected_type=int)
        self.longueur_max = self.get_config("conveyor.max_length", default=20, expected_type=int)

        # Paramètres distributions 
        self.default_sigma = self.get_config("distributions.normal.default_sigma", default=20, expected_type=int)

        self.default_lambda = self.get_config("distributions.poisson.default_lambda", default=0.03, expected_type=float)

        self.default_alpha = self.get_config("distributions.beta.default_alpha", default=1, expected_type=int)
        self.default_beta = self.get_config("distributions.beta.default_beta", default=3, expected_type=int)

        self.default_mu = self.get_config("distributions.binomialnegatif.default_mu", default=8, expected_type=int)
        self.default_k = self.get_config("distributions.binomialnegatif.default_k", default=4, expected_type=int)

        self.default_early_mean = self.get_config("distributions.bimodal.early_mean", default=90, expected_type=int)
        self.default_early_std = self.get_config("distributions.bimodal.early_std", default=20, expected_type=float)
        self.default_late_mean = self.get_config("distributions.bimodal.late_mean", default=45, expected_type=int)
        self.default_late_std = self.get_config("distributions.bimodal.late_std", default=15, expected_type=int)
        self.default_early_weight = self.get_config("distributions.bimodal.early_weight", default=0.7, expected_type=float)

        self.default_lognormal_mu = self.get_config("distributions.lognormal.default_mu", default=4.0, expected_type=float)
        self.default_lognormal_sigma = self.get_config("distributions.lognormal.default_sigma", default=0.5, expected_type=float)

        self.default_gamma_shape = self.get_config("distributions.gamma.default_shape", default=2.0, expected_type=float)
        self.default_gamma_scale = self.get_config("distributions.gamma.default_scale", default=30.0, expected_type=float)

        self.default_weibull_shape = self.get_config("distributions.weibull.default_shape", default=1.5, expected_type=float)
        self.default_weibull_scale = self.get_config("distributions.weibull.default_scale", default=60.0, expected_type=float)

        self.default_trimodal_means = self.get_config("distributions.trimodal.means", default=[150, 120, 90], expected_type=list)
        self.default_trimodal_stds = self.get_config("distributions.trimodal.stds", default=[20, 15, 10], expected_type=list)
        self.default_trimodal_weights = self.get_config("distributions.trimodal.weights", default=[0.5, 0.3, 0.2], expected_type=list)

        self.default_pareto_alpha = self.get_config("distributions.pareto.default_alpha", default=2.0, expected_type=float)
        self.default_pareto_scale = self.get_config("distributions.pareto.default_scale", default=30.0, expected_type=float)

        # Paramètres distributions 
        self.info_globaux = self.get_config("informations.globaux", default="", expected_type=str)
        self.info_uniform = self.get_config("informations.uniform", default="", expected_type=str)
        self.info_normal  = self.get_config("informations.normal", default="", expected_type=str)
        self.info_binomialnegatif = self.get_config("informations.binomialnegatif", default="", expected_type=str)
        self.info_poisson = self.get_config("informations.poisson", default="", expected_type=str)
        self.info_beta = self.get_config("informations.beta", default="", expected_type=str)
        self.info_bimodal = self.get_config("informations.bimodal", default="", expected_type=str)
        self.info_lognormal = self.get_config("informations.lognormal", default="", expected_type=str)
        self.info_gamma = self.get_config("informations.gamma", default="", expected_type=str)
        self.info_weibull = self.get_config("informations.weibull", default="", expected_type=str)
        self.info_trimodal = self.get_config("informations.trimodal", default="", expected_type=str)
        self.info_pareto = self.get_config("informations.pareto", default="", expected_type=str)

    def get_config(self, keys, default=None, expected_type=None):
        """Méthode helper pour récupérer les valeurs de configuration"""
        if isinstance(keys, str):
            keys = keys.split('.')
        
        value = self.config
        try:
            for key in keys:
                value = value[key]
        except (KeyError, TypeError):
            return default
        
        if expected_type is not None and not isinstance(value, expected_type):
            try:
                return expected_type(value)
            except (ValueError, TypeError):
                return default
        
        return value

    def __repr__(self):
        params_list = []
        for attr, value in vars(self).items():
            params_list.append(f"{attr}={value}")
        return "Params(" + ", ".join(params_list) + ")"
