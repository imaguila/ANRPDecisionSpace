PROBLEMAS = {

    "CLASSIC Dataset": {
        "path_sol": "data/BAGNALL/bagnallsoluciones.txt",
        "path_prob": "data/BAGNALL/bagnalldataset.txt",
        "metricas": ["satisfaction", "effort"],
        "num_req": 18,
        "stakeholders_prefix": "c",
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
        ],
        "paper": "Greer, D., & Ruhe, G. (2004). Software release planning: an evolutionary and iterative approach. Information and software technology, 46(4), 243-253.",
    },
    "MSLite System": {
        "path_sol": "data/MSLITE/mslitesoluciones.txt",
        "path_prob": None,
        "metricas": ["satisfaction", "effort", "dissatisfaction"],
        "num_req": 16,
        "stakeholders_prefix": None,
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
            "annoyance",
            "dirtiness",
        ],
        "paper": "Sangwan, R. S., Negahban, A., Nord, R. L., & Ozkaya, I. (2020). Optimization of software release planning considering architectural dependencies, cost, and value. IEEE Transactions on Software Engineering, 48(4), 1369-1384.",
    },


    "Replacement Access, Library and ID Card (RALIC)": {
        "path_sol": "data/RALICSreq/ralicsreqsoluciones.txt",
        "path_prob": "data/RALICSreq/ralicsreqdataset.txt",
        "metricas": ["satisfaction", "effort"],
        "num_req": 83,
        "stakeholders_prefix": "c", 
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
        ],
        "paper": "Lim, S. L., & Finkelstein, A. (2011). StakeRare: using social networks and collaborative filtering for large-scale requirements elicitation. IEEE transactions on software engineering, 38(3), 707-735.",
    },

    "Word processing software project": {
        "path_sol": "data/WORDPROC/wordprocsoluciones.txt",
        "path_prob": "data/WORDPROC/wordprocdataset.txt",
        "metricas": ["satisfaction", "effort", "time"],
        "num_req": 42,
        "stakeholders_prefix": "cv",  # 👈 DIFERENTE
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
            "response",
            "opportunity",
        ],
        "paper": "Agarwal, N., Karimpour, R., & Ruhe, G. (2014, January). Theme-based product release planning: An analytical approach. In 2014 47th Hawaii International Conference on System Sciences (pp. 4739-4748). IEEE.",
    },
    "Large dataset": {
        "path_sol": "data/REQ100/req100frente.txt",
        "path_prob": "data/REQ100/req100dataset.txt",
        "metricas": ["satisfaction", "effort"],
        "num_req": 96,
        "stakeholders_prefix": "c",
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
        ],
        "paper": "Del Sagrado, J., Del Águila, I. M., & Orellana, F. J. (2015). Multi-objective ant colony optimization for requirements selection. Empirical Software Engineering, 20(3), 577-610.",
    },
    "ReleasePlanner™ dataset": {
        "path_sol": "data/THEME/themesoluciones.txt",
        "path_prob": "data/THEME/themedataset.txt",
        "metricas": [
            "satisfaction", "prevalence", "cost",
            "dissatisfaction", "inestability", "effort"
        ],
        "num_req": 22,
        "stakeholders_prefix": "c",
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
            "effectiveness",
            "dirtiness",
            "annoyance",
            "stickiness",
            "fragility",
            "robustness",
            "usage_efficiency",
        ],
        "paper": "Karim, M. R., & Ruhe, G. (2014, August). Bi-objective genetic search for release planning in support of themes. In International Symposium on Search Based Software Engineering (pp. 123-137). Cham: Springer International Publishing.",
    },
    "Motorola Dataset": {
        "path_sol": "data/MOTOROLA/motorolasoluciones.txt",
        "path_prob": "data/MOTOROLA/motoroladataset.txt",
        "metricas": ["satisfaction", "effort"],
        "num_req": 35,
        "stakeholders_prefix": "c",
        "indicadores_default": [
            "scope",
            "productivity",
            "squandering",
        ],
        "paper": "Baker, P., Harman, M., Steinhofel, K., & Skaliotis, A. (2006, September). Search based approaches to component selection and prioritization for the next release problem. In 2006 22nd IEEE International Conference on Software Maintenance (pp. 176-185). IEEE.",
    }
}