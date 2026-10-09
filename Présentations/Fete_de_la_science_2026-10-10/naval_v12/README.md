# Recalcul Naval — Morse HGP v12

Le résultat a été calculé avec le moteur **Morse HGP 3D v12**, commit `ac2d5bab814e84db6e1c9340f54995aa9cda58aa`, sans modifier ses 52 unités CPU.

330 543 points originaux sont conservés dans la zone montrée. Les a priori géométriques expliquent 290 878 points par les 14 références AABB et 15 791 autres par le contexte `Background` (distance aux 104 triangles ≤ 3 cm). Le moteur reçoit tous les **23 874 résidus**, sans sous-échantillonnage. Sa tour complète K=1 à 3 est calculée ; la figure montre cinq couvertures de composantes K=3 à rayon 4 cm, avec au moins 200 points chacune.

Ces couvertures sont une lecture externe des incidences fortes des vraies composantes continues. Elles ne sont pas la projection Hᵣ, encore absente de v12. Les a priori filtrent l’entrée avant le calcul ; ils ne constituent pas une nouvelle API native v12. Le rapport donne les paramètres, limites et validations.

- `result.npz` : toutes les coordonnées de la zone, leurs indices dans le scan original, masques de prétraitement et couleurs des composantes retenues.
- `full.bin.gz` : la véritable tour native au format FUL1 ; SHA256 décompressé `12c1fa3a52ba11633b9bf514f44c16727adc19e366a3d41c082d480bead4d2a9`.
- `cut_membership.npz` : incidences site–nœud dédupliquées à la coupe, masses et cinq nœuds retenus.
- `naval_v12_report.json` : provenance, méthode, paramètres et empreintes.

## Rejouer le calcul natif

Python avec NumPy et g++ C++20 sont nécessaires. Utiliser un dossier de travail neuf et vide :

```bash
python reproduce.py --work-dir /tmp/naval-v12-replay
```

Le script télécharge les sources à la révision épinglée, vérifie leurs hashes Git, compile le moteur inchangé, rejoue les 23 874 entrées originales géométriquement filtrées et vérifie le digest FUL1 ainsi que tous les membres de chaque candidat. Les étiquettes publiées servent seulement à vérifier le résultat, après sa recomputation. Pour utiliser des sources déjà téléchargées :

```bash
python reproduce.py --source-dir /chemin/morsehgp3D_v12 --work-dir /tmp/naval-v12-replay
```

Le runner rejoue le **snapshot de l’entrée filtrée** enregistré dans `result.npz`. Les scripts `prepare_data.py` et `prepare_background.py` conservent la préparation originale à partir du scan/maillage. Leurs fichiers bruts et métadonnées sont listés dans `data_source_manifest.json`, `data_model_analysis.json` et `data_bloc_components.npz` ; ils ne sont pas téléchargés par le runner de replay. Les sources sont celles du benchmark synthétique de Marie Aspro, et aucun maillage `Anomaly_*` n’a servi aux priors ou à la sélection.

L’export des diagnostics et l’export natif FUL1 utilisent deux clients séparés : `export_prior.cpp` puis `export_full_only.cpp`. Les tableaux publiés ont été vérifiés indépendamment, notamment leurs identifiants, leur coupe rationnelle exacte et l’absence de recouvrement entre les cinq groupes retenus.
