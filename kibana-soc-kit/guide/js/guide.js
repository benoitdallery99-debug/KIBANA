/* Guide interactif — JavaScript vanilla, sans dépendance.
   Tout est local : le guide ne fait aucune requête réseau, jamais. */
(function () {
  "use strict";

  /* ------------------------------------------------------------------ */
  /* Stockage local : toujours sous try/catch.                           */
  /* En navigation privée, avec les données de site bloquées, ou dans    */
  /* une capture de vignette, l'accès peut lever. Le guide doit alors    */
  /* fonctionner quand même, simplement sans mémoire.                    */
  /* ------------------------------------------------------------------ */
  var CLE = "kit-soc-kibana";
  var memoire = null;

  function lire() {
    if (memoire) return memoire;
    memoire = { faits: {}, theme: null, resolus: {} };
    try {
      var brut = window.localStorage.getItem(CLE);
      if (brut) {
        var d = JSON.parse(brut);
        memoire.faits = d.faits || {};
        memoire.theme = d.theme || null;
        memoire.resolus = d.resolus || {};
      }
    } catch (e) { /* stockage indisponible : on continue sans mémoire */ }
    return memoire;
  }

  function ecrire() {
    try {
      window.localStorage.setItem(CLE, JSON.stringify(lire()));
    } catch (e) { /* idem */ }
  }

  /* ------------------------------------------------------------------ */
  /* Normalisation — doit reproduire EXACTEMENT celle de                 */
  /* data/generateur/engendrer.py : sinon une réponse juste serait       */
  /* refusée, ce qui est le pire défaut possible pour un stagiaire.      */
  /* ------------------------------------------------------------------ */
  function normaliser(valeur, regle) {
    var t = String(valeur).trim();
    if (regle.indexOf("minuscules") !== -1) t = t.toLowerCase();
    if (regle.indexOf("accents retirés") !== -1) {
      t = t.normalize("NFD").replace(/[̀-ͯ]/g, "");
    }
    if (regle.indexOf("espaces retirés") !== -1) {
      t = t.split(/\s+/).filter(Boolean).join(" ");
    }
    return t;
  }

  /* ------------------------------------------------------------------ */
  /* SHA-256. crypto.subtle n'est pas garanti en file:// selon les       */
  /* navigateurs : on prévoit un repli en JavaScript pur.                */
  /* ------------------------------------------------------------------ */
  var K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
  ];

  function sha256Pur(message) {
    function rotr(x, n) { return (x >>> n) | (x << (32 - n)); }
    var octets = [];
    for (var i = 0; i < message.length; i++) {
      var c = message.charCodeAt(i);
      if (c < 0x80) octets.push(c);
      else if (c < 0x800) octets.push(0xc0 | (c >> 6), 0x80 | (c & 63));
      else if (c < 0xd800 || c >= 0xe000) {
        octets.push(0xe0 | (c >> 12), 0x80 | ((c >> 6) & 63), 0x80 | (c & 63));
      } else {
        i++;
        var p = 0x10000 + (((c & 0x3ff) << 10) | (message.charCodeAt(i) & 0x3ff));
        octets.push(0xf0 | (p >> 18), 0x80 | ((p >> 12) & 63),
                    0x80 | ((p >> 6) & 63), 0x80 | (p & 63));
      }
    }
    var bits = octets.length * 8;
    octets.push(0x80);
    while (octets.length % 64 !== 56) octets.push(0);
    for (var j = 7; j >= 0; j--) octets.push((bits / Math.pow(2, j * 8)) & 0xff);

    var h = [0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,
             0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19];
    var w = new Array(64);
    for (var bloc = 0; bloc < octets.length; bloc += 64) {
      for (var t = 0; t < 16; t++) {
        w[t] = (octets[bloc + t * 4] << 24) | (octets[bloc + t * 4 + 1] << 16) |
               (octets[bloc + t * 4 + 2] << 8) | octets[bloc + t * 4 + 3];
      }
      for (t = 16; t < 64; t++) {
        var s0 = rotr(w[t-15],7) ^ rotr(w[t-15],18) ^ (w[t-15] >>> 3);
        var s1 = rotr(w[t-2],17) ^ rotr(w[t-2],19) ^ (w[t-2] >>> 10);
        w[t] = (w[t-16] + s0 + w[t-7] + s1) | 0;
      }
      var a=h[0],b=h[1],c=h[2],d=h[3],e=h[4],f=h[5],g=h[6],hh=h[7];
      for (t = 0; t < 64; t++) {
        var S1 = rotr(e,6) ^ rotr(e,11) ^ rotr(e,25);
        var ch = (e & f) ^ (~e & g);
        var t1 = (hh + S1 + ch + K[t] + w[t]) | 0;
        var S0 = rotr(a,2) ^ rotr(a,13) ^ rotr(a,22);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var t2 = (S0 + maj) | 0;
        hh=g; g=f; f=e; e=(d+t1)|0; d=c; c=b; b=a; a=(t1+t2)|0;
      }
      h[0]=(h[0]+a)|0; h[1]=(h[1]+b)|0; h[2]=(h[2]+c)|0; h[3]=(h[3]+d)|0;
      h[4]=(h[4]+e)|0; h[5]=(h[5]+f)|0; h[6]=(h[6]+g)|0; h[7]=(h[7]+hh)|0;
    }
    return h.map(function (x) {
      return ("00000000" + (x >>> 0).toString(16)).slice(-8);
    }).join("");
  }

  function empreinte(texte) {
    if (window.crypto && window.crypto.subtle && window.TextEncoder) {
      try {
        return window.crypto.subtle
          .digest("SHA-256", new TextEncoder().encode(texte))
          .then(function (tampon) {
            return Array.prototype.map
              .call(new Uint8Array(tampon), function (o) {
                return ("0" + o.toString(16)).slice(-2);
              })
              .join("");
          })
          .catch(function () { return sha256Pur(texte); });
      } catch (e) { /* on bascule sur le repli */ }
    }
    return Promise.resolve(sha256Pur(texte));
  }

  /* ------------------------------------------------------------------ */
  /* Thème                                                               */
  /* ------------------------------------------------------------------ */
  function appliquerTheme(theme) {
    if (theme) document.documentElement.setAttribute("data-theme", theme);
    else document.documentElement.removeAttribute("data-theme");
  }

  function initTheme() {
    var etat = lire();
    appliquerTheme(etat.theme);
    var bouton = document.getElementById("bascule-theme");
    if (!bouton) return;
    function libelle() {
      var e = lire();
      bouton.textContent = e.theme === "sombre" ? "Thème clair"
                        : e.theme === "clair" ? "Thème système"
                        : "Thème sombre";
    }
    libelle();
    bouton.addEventListener("click", function () {
      var e = lire();
      e.theme = e.theme === "sombre" ? "clair" : e.theme === "clair" ? null : "sombre";
      appliquerTheme(e.theme);
      ecrire();
      libelle();
    });
  }

  /* ------------------------------------------------------------------ */
  /* Copier une requête                                                  */
  /* ------------------------------------------------------------------ */
  function initCopie() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-copier]"),
      function (bouton) {
        bouton.addEventListener("click", function () {
          var cible = document.getElementById(bouton.getAttribute("data-copier"));
          if (!cible) return;
          var texte = cible.textContent;
          var fini = function (ok) {
            bouton.textContent = ok ? "Requête copiée" : "Copie impossible";
            bouton.setAttribute("data-etat", ok ? "fait" : "");
            window.setTimeout(function () {
              bouton.textContent = "Copier";
              bouton.removeAttribute("data-etat");
            }, 2000);
          };
          if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(texte).then(function () { fini(true); },
                                                      function () { fini(false); });
          } else {
            try {
              var z = document.createElement("textarea");
              z.value = texte;
              document.body.appendChild(z);
              z.select();
              fini(document.execCommand("copy"));
              document.body.removeChild(z);
            } catch (e) { fini(false); }
          }
        });
      }
    );
  }

  /* ------------------------------------------------------------------ */
  /* Validation d'une réponse                                            */
  /* Le guide ne connaît que des empreintes : il peut dire « juste » ou  */
  /* « faux », jamais donner la réponse.                                 */
  /* ------------------------------------------------------------------ */
  function initReponses() {
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-exercice]"),
      function (bloc) {
        var champ = bloc.querySelector("input[type=text]");
        var bouton = bloc.querySelector("[data-verifier]");
        var retour = bloc.querySelector(".reponse__retour");
        if (!champ || !bouton || !retour) return;

        var identifiant = bloc.getAttribute("data-exercice");
        var regle = bloc.getAttribute("data-normalisation") || "espaces retirés";
        var attendues = (bloc.getAttribute("data-empreintes") || "").split(",");
        var scenario = bloc.getAttribute("data-scenario") || "";

        function verifier() {
          var saisie = champ.value;
          if (!saisie.trim()) {
            retour.setAttribute("data-etat", "");
            retour.textContent = "Saisissez une réponse avant de vérifier.";
            return;
          }
          empreinte(normaliser(saisie, regle)).then(function (h) {
            var juste = attendues.indexOf(h) !== -1;
            retour.setAttribute("data-etat", juste ? "juste" : "faux");
            retour.textContent = juste
              ? "Réponse vérifiée. Elle correspond à ce que disent les données."
              : "Cette réponse ne correspond pas. Reprenez la requête : "
                + "vérifiez la plage de temps, la data view et le champ interrogé.";
            var etat = lire();
            if (juste) {
              etat.faits[identifiant] = true;
              if (scenario) etat.resolus[scenario] = true;
              ecrire();
              majProgression();
            }
          });
        }

        bouton.addEventListener("click", verifier);
        champ.addEventListener("keydown", function (e) {
          if (e.key === "Enter") { e.preventDefault(); verifier(); }
        });

        if (lire().faits[identifiant]) {
          retour.setAttribute("data-etat", "juste");
          retour.textContent = "Réponse vérifiée lors d'un passage précédent.";
        }
      }
    );
  }

  /* ------------------------------------------------------------------ */
  /* Progression                                                         */
  /* ------------------------------------------------------------------ */
  function majProgression() {
    var etat = lire();
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-jauge-module]"),
      function (jauge) {
        var module = jauge.getAttribute("data-jauge-module");
        var exercices = document.querySelectorAll(
          '[data-exercice][data-module="' + module + '"]'
        );
        var faits = 0;
        Array.prototype.forEach.call(exercices, function (e) {
          if (etat.faits[e.getAttribute("data-exercice")]) faits++;
        });
        var total = exercices.length;
        // Un compte chiffre plutot que des pastilles : les glyphes geometriques
        // manquent a la police et tombaient en repli, donnant un signe illisible.
        // Le chiffre se lit aussi a l'impression et par un lecteur d'ecran.
        jauge.textContent = total ? faits + "/" + total : "—";
        jauge.setAttribute(
          "aria-label",
          total ? faits + " exercice(s) sur " + total + " validés" : "aucun exercice"
        );
      }
    );
    Array.prototype.forEach.call(
      document.querySelectorAll("[data-enquete]"),
      function (case_) {
        var s = case_.getAttribute("data-enquete");
        case_.setAttribute("data-resolu", etat.resolus[s] ? "oui" : "non");
      }
    );
  }

  /* ------------------------------------------------------------------ */
  /* Position courante dans le sommaire                                  */
  /* ------------------------------------------------------------------ */
  function initPosition() {
    var cibles = document.querySelectorAll("[data-ancre]");
    if (!cibles.length || !window.IntersectionObserver) return;
    var liens = {};
    Array.prototype.forEach.call(
      document.querySelectorAll(".sommaire a[href^='#']"),
      function (a) { liens[a.getAttribute("href").slice(1)] = a; }
    );
    var visibles = {};
    var observateur = new IntersectionObserver(function (entrees) {
      entrees.forEach(function (e) { visibles[e.target.id] = e.isIntersecting; });
      var courant = null;
      Array.prototype.forEach.call(cibles, function (c) {
        if (visibles[c.id] && !courant) courant = c.id;
      });
      Object.keys(liens).forEach(function (id) {
        if (id === courant) liens[id].setAttribute("aria-current", "true");
        else liens[id].removeAttribute("aria-current");
      });
    }, { rootMargin: "-10% 0px -75% 0px" });
    Array.prototype.forEach.call(cibles, function (c) { observateur.observe(c); });
  }

  /* ------------------------------------------------------------------ */
  /* Recherche plein texte                                               */
  /* ------------------------------------------------------------------ */
  function initRecherche() {
    var champ = document.getElementById("recherche");
    var compteur = document.getElementById("recherche-resultats");
    if (!champ) return;
    var sections = document.querySelectorAll("[data-cherchable]");

    champ.addEventListener("input", function () {
      var q = champ.value.trim().toLowerCase();
      var trouves = 0;
      Array.prototype.forEach.call(sections, function (s) {
        if (!q) { s.hidden = false; return; }
        var dedans = s.textContent.toLowerCase().indexOf(q) !== -1;
        s.hidden = !dedans;
        if (dedans) trouves++;
      });
      if (compteur) {
        compteur.textContent = !q
          ? ""
          : trouves === 0
            ? "Aucune section ne contient ce mot."
            : trouves + " section(s) trouvée(s).";
      }
    });
  }

  /* ------------------------------------------------------------------ */
  /* Sommaire repliable sur petit écran                                  */
  /* ------------------------------------------------------------------ */
  function initSommaire() {
    var bascule = document.getElementById("bascule-sommaire");
    var sommaire = document.querySelector(".sommaire");
    if (!bascule || !sommaire) return;
    function poser(ouvert) {
      sommaire.setAttribute("data-ouvert", ouvert ? "oui" : "non");
      bascule.setAttribute("aria-expanded", ouvert ? "true" : "false");
    }
    poser(window.matchMedia("(min-width: 62rem)").matches);
    bascule.addEventListener("click", function () {
      poser(sommaire.getAttribute("data-ouvert") !== "oui");
    });
  }

  function init() {
    initTheme();
    initSommaire();
    initCopie();
    initReponses();
    initPosition();
    initRecherche();
    majProgression();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
