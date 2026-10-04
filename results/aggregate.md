# Aggregate benchmark results

| Family | Solver | OK/total | Median ms | IQR ms | Max ms |
|---|---|---:|---:|---:|---:|
| correctness_p2 | brute | 1012/1012 | 0.0086825 | 0.00701575 | 0.047875 |
| correctness_p2 | tw-dp | 1012/1012 | 0.314195 | 0.434246 | 12.985 |
| forest_dense | forest-dense | 4/4 | 0.0582405 | 0.193991 | 0.520347 |
| forest_dense | forest-paper | 4/4 | 0.294056 | 2.11696 | 6.95699 |
| forest_dense | forest-sparse | 4/4 | 0.162947 | 0.645427 | 1.80504 |
| ttsp_diamond | brute | 24/24 | 0.010411 | 0.0226002 | 0.128136 |
| ttsp_diamond | ttsp-transfer | 63/63 | 0.311447 | 1.71221 | 255.522 |
