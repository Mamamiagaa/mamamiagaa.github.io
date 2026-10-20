# mamamiagaa.github.io — site développeur

Ce site sert de vitrine à toutes mes applications Android, avec une page de présentation et une politique de confidentialité pour chacune. Il héberge aussi `app-ads.txt` pour AdMob.

- Hébergement **gratuit** sur GitHub Pages : pas de serveur, pas de VPS, pas de maintenance.
- Les applications elles-mêmes n'ont **pas** besoin de ce site pour fonctionner. Il n'est exigé que par Google Play (URL de la politique de confidentialité) et par AdMob (`app-ads.txt`).

```
site.json               réglages communs : éditeur, e-mail, ID éditeur AdMob
apps/<slug>/app.json    fiche d'une app (nom, package, textes fr/en/es, statut)
apps/<slug>/privacy.md  politique de confidentialité (fr/en/es) avec {{variables}}
apps/<slug>/assets/     icône, bannières
apps/_template/         modèle à copier pour une nouvelle app (ignoré par le build)
src/assets/             CSS et police partagés
build.py                générateur (Python 3, sans dépendance)
docs/                   SITE GÉNÉRÉ, publié par GitHub Pages (ne pas éditer à la main)
```

Adresses publiques produites :

| URL | Usage |
|---|---|
| `https://mamamiagaa.github.io/` | liste des applications |
| `https://mamamiagaa.github.io/<slug>/` (+ `/en/`, `/es/`) | page de l'app ; champ **Site web** de la fiche Play |
| `https://mamamiagaa.github.io/<slug>/privacy/` | champ **Règles de confidentialité** de Play Console |
| `https://mamamiagaa.github.io/app-ads.txt` | AdMob, un seul fichier pour toutes les apps |

## 1. Première mise en ligne (une seule fois)
1. Renseigner `publisher_name` (nom de l'éditeur) dans `site.json`.
2. Lancer `python build.py`. La commande doit afficher « OK ».
3. Sur github.com, créer un dépôt **public** nommé exactement `mamamiagaa.github.io`, sans README.
4. Pousser ce dossier :
   ```
   git remote add origin https://github.com/mamamiagaa/mamamiagaa.github.io.git
   git push -u origin main
   ```
5. Sur GitHub, ouvrir le dépôt, aller dans **Settings › Pages**, choisir *Deploy from a branch*, puis *main* et le dossier */docs*, et enregistrer.
6. Attendre une à deux minutes, puis ouvrir `https://mamamiagaa.github.io/`.

## 2. Ajouter une nouvelle application (environ 10 minutes)
1. Copier `apps/_template` vers `apps/<slug>`, où `<slug>` est le nom de l'app en minuscules sans espaces, par exemple `apps/monapp`.
2. Dans `app.json`, remplir :
   - `name`, `package` (identique à l'`applicationId` Android), `accent` ;
   - les textes en fr/en/es ;
   - les dates.
3. Mettre dans `assets/` :
   - `icon.png`, carré, 512 px ou plus ;
   - `feature-fr.png`, `feature-en.png` et `feature-es.png` (1024×500, les mêmes que sur Play).
4. Écrire `privacy.md` en décrivant **exactement** ce que fait l'app. Si l'app utilise aussi AdMob ou Play Billing, partir de `apps/listo/privacy.md`. Variables disponibles : `{{app_name}}`, `{{package}}`, `{{publisher_name}}`, `{{contact_email}}`, `{{effective_date}}`, `{{updated_date}}`, `{{site_url}}`.
5. Si l'app utilise un autre compte AdMob, ajouter son `pub-…` dans `admob_publisher_ids` de `site.json`.
6. Vérifier en local :
   ```
   python build.py --serve
   ```
   puis ouvrir http://localhost:8000.
7. Générer pour de bon, puis publier :
   ```
   python build.py
   git add -A
   git commit -m "Add <slug>"
   git push
   ```
8. Dans Play Console, coller l'URL `https://mamamiagaa.github.io/<slug>/privacy/` comme politique de confidentialité, et `https://mamamiagaa.github.io/<slug>/` comme site web.

Quand l'app est en ligne sur Play, passer `"status"` à `"published"` : le bouton « Disponible sur Google Play » apparaît.

## 3. Mettre à jour une politique
1. Modifier `privacy.md`, puis changer `updated_date` dans `app.json`.
2. Relancer `python build.py` et pousser.
3. L'URL ne change pas : rien à refaire dans Play Console.

Si une fonctionnalité change les données collectées (un nouveau SDK, des analytics…), mettre aussi à jour la section **Data safety** dans Play Console.

## 4. Garde-fous du générateur
`python build.py` **refuse** de produire le site, et ne touche pas à `docs/`, dans les cas suivants :
- `publisher_name` est vide ;
- l'e-mail est invalide ;
- un identifiant AdMob est mal formé ;
- un texte manque dans une langue ;
- une variable `{{…}}` est inconnue ;
- il reste « À COMPLÉTER » ou « TODO » dans une politique.

L'option `--draft` permet un aperçu local, avec un bandeau rouge « BROUILLON ». Ne publiez jamais un build `--draft`.

La politique de confidentialité est rédigée à partir du fonctionnement réel de l'app. Ce n'est pas un conseil juridique : faites-la relire si nécessaire.
