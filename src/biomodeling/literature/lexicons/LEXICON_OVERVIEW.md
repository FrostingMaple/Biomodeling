# 生物数学建模词典总览

- 生成日期：2026-09-29
- 总条目数：125
- 数据来源：16 个来源

## 词典构成

| 词典 | 条目数 | JSON | Markdown |
| --- | ---: | --- | --- |
| parameters | 40 | `parameters.json` | `parameters.md` |
| relations | 31 | `relations.json` | `relations.md` |
| expressions | 29 | `expressions.json` | `expressions.md` |
| models | 25 | `models.json` | `models.md` |

## 来源清单

| europepmc | Europe PMC REST API | https://www.ebi.ac.uk/europepmc/webservices/rest/search |
| biomodels | BioModels curated model repository | https://www.ebi.ac.uk/biomodels/ |
| biomodels_search | BioModels kinetic model search response | https://www.ebi.ac.uk/biomodels/search |
| sbml | Systems Biology Markup Language (SBML) | https://sbml.org/ |
| reactome | Reactome Content Service | https://reactome.org/ContentService/ |
| sabio_rk | SABIO-RK reaction kinetics database | https://sabio.h-its.org/ |
| brenda | BRENDA enzyme database | https://www.brenda-enzymes.org/ |
| kegg | KEGG pathway database | https://www.genome.jp/kegg/ |
| classic_mm | Michaelis and Menten enzyme kinetics | https://doi.org/10.1016/S0076-6879(09)63002-7 |
| classic_hh | Hodgkin and Huxley action potential model | https://doi.org/10.1113/jphysiol.1952.sp004764 |
| classic_sir | Kermack and McKendrick compartmental epidemic model | https://doi.org/10.1098/rspa.1927.0118 |
| classic_lotka_volterra | Lotka-Volterra population dynamics | https://doi.org/10.1038/140070a0 |
| repressilator | Elowitz and Leibler repressilator | https://doi.org/10.1038/35002125 |
| mapk_cascade | Kholodenko MAPK cascade oscillation model | https://doi.org/10.1046/j.1432-1327.2000.01197.x |
| erbb_model | Chen et al. ErbB signaling mass-action model | https://doi.org/10.1038/msb.2008.74 |
| hepatic_glucose | Konig et al. human hepatic glucose metabolism model | https://doi.org/10.1371/journal.pcbi.1002577 |

## 查询命令

```powershell
py -m src.bio_variable_extractor lexicon
py -m src.bio_variable_extractor lexicon parameters --id PARAM_KM
py -m src.bio_variable_extractor lexicon expressions --search "Michaelis"
py -m src.bio_variable_extractor lexicon models --search "repressilator"
```

## 使用约束

- 词典用于识别、归一化和上下文提示，不替代单篇文献证据。
- 每个变量或关系仍必须绑定原文证据块。
- 符号冲突保留显式消歧，不强制合并。