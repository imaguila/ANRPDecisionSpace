PROBLEMAS = {

    "BAGNALL": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    },

    "MSLITE": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    },

    "RALICSREQ": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    },

    "WORDPROC": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    },
    "REQ100": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    },
    "THEME": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    },
    "MOTOROLA": {
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
        "paper": "Bagnall, A. J., Rayward-Smith, V. J., & Whittley, I. M. (2001). The next release problem. Information and software technology, 43(14), 883-890.",
    }
}