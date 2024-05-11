# Felhők hálózati szolgáltatásai labor HF 

[![Actions Status](https://github.com/Peszog/fehszo-hf/workflows/actions/badge.svg)](https://github.com/Peszog/fehszo-hf/actions)

Ez a repo tartalmazza a Felhők hálózati szolgáltatásai labor tárgyhoz készített házi feladatot.
## Feladat kiírás:
A félév során mindenkinek létre kell hoznia egy fejlesztői CI/CD környezetet a saját gépén és ennek használatával egy olyan web szolgáltatást kell létrehozni ami az alábbi funkciókat látja el:

Kép és hozzá tartozó leírás feltöltése (kép és leírás páros tárolás)

A feltöltött képen automatikus autó detektálás és a megtalált autók bekeretezésével a kép megjelenítése a weboldalon

A weboldal “üzemeltetői” képesek legyenek feliratkozni az oldalra, azaz kapjanak értesítést az összes eddigi és az új feltöltött képekről úgy, hogy kiküldésre kerül számukra a képhez tartozó leírás és a rendszer által detektált autók száma a feltöltött képen

## Futtatási környezet
Python Flask alapú webszerver dockerizálva, Kafka.
Minikube és argocd alkalmazása a repository felügyeletére kubernetessel, Ubuntu 22.04-en futtatva.

## Architektúra
ArgoCD
- Loadbalancer ami összeköti a webszervert és a kafka brokert
- webszerver deployment
- kafka StatefulSet

## Futtatáshoz
ArgoCD alkalmazás létrehozása után manuálisan létre kell hozni a "serverUploads" topicot, ugyanis a szerver oda küldi az üzeneteket.