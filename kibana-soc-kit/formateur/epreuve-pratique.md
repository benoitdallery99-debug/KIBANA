# Épreuve pratique — 30 minutes

**À remettre au stagiaire. Ce document ne contient aucune réponse.**

Jeu de données : `epreuve-logs` (motif `logs-*-epreuve`). Ce n'est **pas** celui
du parcours : les structures sont les mêmes, les réponses sont différentes. Rien
de ce que vous avez noté pendant la journée ne s'y applique.

---

## La situation

Il est 9 h 10. Le chef de salle passe vous voir : le comité de direction se
réunit à 10 h et il doit y apporter trois réponses. Il ne veut pas de capture
d'écran envoyée à la volée : il veut **un tableau de bord** qu'il pourra rouvrir
seul, la semaine prochaine, sans vous.

Vous avez trente minutes.

## Ce qu'on vous demande

Construisez **un seul tableau de bord**, nommé `Épreuve — <votre nom>`, qui
répond à ces trois questions :

1. **La collecte est-elle complète ?** Une source a cessé d'émettre. Le tableau
   doit permettre de le voir sans lire une requête, et de dire laquelle.
2. **Sommes-nous attaqués depuis l'extérieur ?** Une adresse extérieure s'est
   acharnée sur un compte. Le tableau doit montrer laquelle, et sur quel compte.
3. **Quelque chose sort-il de l'organisation ?** Un poste a envoyé un volume
   inhabituel vers l'extérieur, de nuit. Le tableau doit le faire ressortir.

## Contraintes

- Le tableau de bord porte au plus **huit panneaux**.
- Chaque titre de panneau est **une question**, pas un nom de champ.
- Votre nom figure dans le titre du tableau de bord.
- Vous travaillez sur la data view `epreuve-logs`. Si vous travaillez sur une
  autre, votre tableau ne montrera rien de ce qu'on vous demande.
- Vous pouvez tout consulter : le guide, votre fiche mémo, vos notes, la
  documentation. Ce n'est pas un examen de mémoire.

## Rendu

À la fin des trente minutes :
1. Enregistrez votre tableau de bord.
2. Écrivez ci-dessous, en **cinq lignes au plus**, ce que vous diriez au chef de
   salle. Pas ce que vous avez fait : ce qu'il doit retenir, et ce que vous lui
   recommandez de décider.

```
_______________________________________________________________________

_______________________________________________________________________

_______________________________________________________________________

_______________________________________________________________________

_______________________________________________________________________
```

## Comment vous serez évalué

Sur ce que vous rendez, pas sur la manière d'y arriver. Le barème est au dos de
la feuille du formateur ; il porte sur quatre points : les trois questions ont
une réponse lisible dans le tableau, les titres sont des questions, le tableau
est réutilisable sans vous, et la synthèse est utile à quelqu'un qui n'a pas
ouvert Kibana.

**Un conseil, le même qu'en salle** : si un écran est vide, vérifiez la data
view, puis la plage de temps, puis le langage de requête. Dans cet ordre.
