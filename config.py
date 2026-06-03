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

}