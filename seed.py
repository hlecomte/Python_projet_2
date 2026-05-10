"""
Script de peuplement de la base de données.
Crée un admin, un étudiant de test, 100+ questions IT, et un quiz d'exemple.
Usage : python seed.py
"""
import pyotp
from datetime import datetime, timedelta
from app import app, db
from models import User, Question, Option, ScheduledQuiz
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt(app)

# ─── Données de questions ─────────────────────────────────────────────────────
# Format : (texte_question, catégorie, difficulté, [optA, optB, optC, optD], lettre_correcte)

QUESTIONS = [
    # ───── RÉSEAUX (25) ─────
    ("Combien de couches possède le modèle OSI ?",
     "Réseaux", "facile",
     ["4 couches", "5 couches", "7 couches", "9 couches"], "c"),

    ("Quel protocole permet la résolution de noms de domaine en adresses IP ?",
     "Réseaux", "facile",
     ["DHCP", "DNS", "FTP", "SMTP"], "b"),

    ("À quelle couche OSI correspond le protocole TCP ?",
     "Réseaux", "normal",
     ["Couche Réseau (3)", "Couche Application (7)", "Couche Transport (4)", "Couche Liaison (2)"], "c"),

    ("Quel port utilise le protocole HTTP par défaut ?",
     "Réseaux", "facile",
     ["Port 21", "Port 22", "Port 80", "Port 443"], "c"),

    ("Quel est le masque de sous-réseau correspondant au préfixe /24 ?",
     "Réseaux", "normal",
     ["255.0.0.0", "255.255.0.0", "255.255.255.0", "255.255.255.128"], "c"),

    ("Quelle est l'adresse de loopback IPv4 ?",
     "Réseaux", "facile",
     ["192.168.1.1", "127.0.0.1", "0.0.0.0", "255.255.255.255"], "b"),

    ("Quel protocole est utilisé pour l'attribution automatique d'adresses IP ?",
     "Réseaux", "facile",
     ["DNS", "ARP", "DHCP", "ICMP"], "c"),

    ("Quel port utilise HTTPS ?",
     "Réseaux", "facile",
     ["Port 80", "Port 8080", "Port 8443", "Port 443"], "d"),

    ("Quelle commande permet de tester la connectivité réseau sous Linux/Windows ?",
     "Réseaux", "facile",
     ["traceroute", "ping", "netstat", "ifconfig"], "b"),

    ("Qu'est-ce que le protocole ARP ?",
     "Réseaux", "normal",
     ["Protocole de routage", "Protocole de chiffrement réseau",
      "Protocole résolvant une IP en adresse MAC", "Protocole de messagerie"], "c"),

    ("Combien de bits contient une adresse IPv4 ?",
     "Réseaux", "facile",
     ["16 bits", "32 bits", "64 bits", "128 bits"], "b"),

    ("Quel protocole de la couche application permet le transfert de fichiers ?",
     "Réseaux", "facile",
     ["HTTP", "FTP", "SMTP", "SNMP"], "b"),

    ("Qu'est-ce qu'un VLAN ?",
     "Réseaux", "normal",
     ["Protocole de sécurité réseau", "Type de câble Ethernet",
      "Réseau local virtuel isolé logiquement", "Algorithme de routage"], "c"),

    ("Quel protocole utilise le port 25 ?",
     "Réseaux", "normal",
     ["POP3", "IMAP", "SMTP", "HTTP"], "c"),

    ("Qu'est-ce que le protocole ICMP est principalement utilisé pour ?",
     "Réseaux", "normal",
     ["Transfert de fichiers", "Messagerie électronique",
      "Diagnostics réseau et messages d'erreur", "Chiffrement des données"], "c"),

    ("Combien de bits contient une adresse IPv6 ?",
     "Réseaux", "normal",
     ["32 bits", "64 bits", "128 bits", "256 bits"], "c"),

    ("Que signifie NAT ?",
     "Réseaux", "normal",
     ["Network Address Translation", "Network Allocation Table",
      "Node Authentication Token", "Network Access Type"], "a"),

    ("Quelle classe d'adresse IP est réservée pour le multicast ?",
     "Réseaux", "difficile",
     ["Classe A", "Classe B", "Classe C", "Classe D"], "d"),

    ("Qu'est-ce qu'un routeur ?",
     "Réseaux", "facile",
     ["Switch qui interconnecte des machines d'un même réseau",
      "Équipement qui interconnecte des réseaux différents",
      "Concentrateur de câbles réseau",
      "Serveur DNS"], "b"),

    ("Quel protocole de couche 4 est sans connexion et privilégie la rapidité ?",
     "Réseaux", "normal",
     ["TCP", "UDP", "ICMP", "ARP"], "b"),

    ("Qu'est-ce qu'un sous-réseau (subnet) ?",
     "Réseaux", "normal",
     ["Type de câble réseau", "Protocole de sécurité",
      "Subdivision logique d'un réseau IP", "Équipement réseau"], "c"),

    ("Quel protocole permet la synchronisation d'horloge réseau ?",
     "Réseaux", "difficile",
     ["SNMP", "NTP", "LDAP", "Kerberos"], "b"),

    ("Qu'est-ce qu'une topologie en étoile ?",
     "Réseaux", "facile",
     ["Réseau circulaire reliant chaque machine à la suivante",
      "Réseau maillé où chaque machine est reliée à toutes",
      "Réseau où toutes les machines sont reliées à un nœud central",
      "Réseau sans fil Wi-Fi"], "c"),

    ("À quelle couche OSI opère un switch (commutateur) ?",
     "Réseaux", "normal",
     ["Couche 1 - Physique", "Couche 2 - Liaison de données",
      "Couche 3 - Réseau", "Couche 4 - Transport"], "b"),

    ("Quel port utilise SSH par défaut ?",
     "Réseaux", "facile",
     ["Port 21", "Port 22", "Port 23", "Port 25"], "b"),

    # ───── SÉCURITÉ (25) ─────
    ("Qu'est-ce que le chiffrement symétrique ?",
     "Sécurité", "normal",
     ["Clé publique différente de la clé privée",
      "La même clé est utilisée pour chiffrer et déchiffrer",
      "Chiffrement sans clé par substitution",
      "Chiffrement utilisant uniquement un hash"], "b"),

    ("Qu'est-ce qu'une attaque SQL Injection ?",
     "Sécurité", "normal",
     ["Attaque réseau par déni de service",
      "Vol de cookies de session",
      "Injection de code SQL malveillant dans les formulaires",
      "Interception de trafic réseau"], "c"),

    ("Qu'est-ce que le hachage (hashing) ?",
     "Sécurité", "normal",
     ["Chiffrement réversible des données",
      "Compression de données pour l'archivage",
      "Transformation irréversible d'une donnée en empreinte de taille fixe",
      "Encodage Base64 réversible"], "c"),

    ("Quelle est la longueur de la clé utilisée par AES-256 ?",
     "Sécurité", "normal",
     ["128 bits", "192 bits", "256 bits", "512 bits"], "c"),

    ("Qu'est-ce qu'une attaque XSS (Cross-Site Scripting) ?",
     "Sécurité", "normal",
     ["Déni de service par saturation de requêtes",
      "Injection de scripts malveillants dans des pages web",
      "Interception de trafic entre client et serveur",
      "Attaque par force brute sur les mots de passe"], "b"),

    ("Que signifie CSRF ?",
     "Sécurité", "difficile",
     ["Cross-Site SQL Injection",
      "Cross-Site Scripting Reverse",
      "Cross-Site Request Forgery",
      "Certificate Signing Request Format"], "c"),

    ("Quel algorithme de hachage est recommandé pour stocker des mots de passe ?",
     "Sécurité", "normal",
     ["MD5", "SHA-1", "SHA-256", "bcrypt"], "d"),

    ("Qu'est-ce qu'un certificat SSL/TLS ?",
     "Sécurité", "normal",
     ["Clé de chiffrement symétrique partagée",
      "Document numérique prouvant l'identité d'un serveur",
      "Protocole de routage sécurisé",
      "Algorithme de signature numérique"], "b"),

    ("Qu'est-ce qu'une attaque Man-in-the-Middle (MitM) ?",
     "Sécurité", "normal",
     ["Attaque par force brute sur un compte",
      "Interception et manipulation des communications entre deux parties",
      "Injection de code dans une base de données",
      "Déni de service distribué"], "b"),

    ("Qu'est-ce que l'authentification à deux facteurs (2FA) ?",
     "Sécurité", "facile",
     ["Utilisation de deux mots de passe différents",
      "Vérification avec deux méthodes d'authentification distinctes",
      "Double chiffrement des données",
      "Deux serveurs d'authentification redondants"], "b"),

    ("Qu'est-ce qu'un pare-feu (firewall) ?",
     "Sécurité", "facile",
     ["Logiciel antivirus temps réel",
      "Réseau privé virtuel chiffré",
      "Dispositif filtrant le trafic réseau selon des règles",
      "Serveur proxy de cache"], "c"),

    ("Qu'est-ce que le phishing ?",
     "Sécurité", "facile",
     ["Virus se propageant via les fichiers exécutables",
      "Tentative de vol d'informations par usurpation d'identité",
      "Attaque réseau par saturation",
      "Injection SQL avancée"], "b"),

    ("Quelle est la différence fondamentale entre RSA et AES ?",
     "Sécurité", "difficile",
     ["RSA est plus rapide qu'AES pour les grands fichiers",
      "RSA est symétrique, AES est asymétrique",
      "RSA est asymétrique, AES est symétrique",
      "Ils utilisent exactement le même algorithme"], "c"),

    ("Qu'est-ce qu'une vulnérabilité zero-day ?",
     "Sécurité", "difficile",
     ["Faille corrigée depuis moins d'un jour",
      "Faille inconnue publiquement sans correctif disponible",
      "Virus découvert le premier jour de sa diffusion",
      "Attaque de type buffer overflow récente"], "b"),

    ("Qu'est-ce que le principe du moindre privilège ?",
     "Sécurité", "normal",
     ["Supprimer tous les droits des utilisateurs standard",
      "Accorder à l'administrateur tous les droits possibles",
      "N'accorder que les droits strictement nécessaires à chaque entité",
      "Partager les droits équitablement entre tous les utilisateurs"], "c"),

    ("Qu'est-ce que la stéganographie ?",
     "Sécurité", "difficile",
     ["Chiffrement militaire à clé secrète",
      "Type de pare-feu applicatif",
      "Technique dissimulant des informations dans d'autres données",
      "Protocole de communication sécurisé"], "c"),

    ("Qu'est-ce qu'une attaque par déni de service (DoS) ?",
     "Sécurité", "facile",
     ["Vol de données sensibles depuis un serveur",
      "Intrusion dans un système via une faille",
      "Saturation d'un service pour le rendre indisponible",
      "Interception du trafic réseau chiffré"], "c"),

    ("Que signifie HTTPS par rapport à HTTP ?",
     "Sécurité", "facile",
     ["HTTP en version 2.0 avec compression",
      "HTTP avec chiffrement SSL/TLS",
      "HTTP sécurisé par un pare-feu applicatif",
      "HTTP avec authentification obligatoire"], "b"),

    ("Qu'est-ce que le salage (salting) d'un mot de passe ?",
     "Sécurité", "difficile",
     ["Chiffrement supplémentaire du hash final",
      "Compression du hash pour réduire sa taille",
      "Ajout d'une valeur aléatoire unique avant le hachage",
      "Application d'un double hachage MD5+SHA"], "c"),

    ("Qu'est-ce qu'une liste blanche (whitelist) en sécurité ?",
     "Sécurité", "normal",
     ["Liste des menaces et malwares connus",
      "Liste des adresses IP bloquées par le pare-feu",
      "Liste des éléments explicitement autorisés",
      "Liste des mots de passe interdits"], "c"),

    ("Qu'est-ce que OAuth 2.0 ?",
     "Sécurité", "difficile",
     ["Protocole de chiffrement symétrique moderne",
      "Standard d'authentification biométrique",
      "Protocole d'autorisation permettant l'accès délégué aux ressources",
      "Algorithme de hachage sécurisé"], "c"),

    ("Qu'est-ce qu'un token JWT ?",
     "Sécurité", "difficile",
     ["Java Web Technology standard",
      "JSON Web Token pour l'authentification sans état (stateless)",
      "Type de cookie de session sécurisé",
      "Protocole d'échange de clés OAuth"], "b"),

    ("Qu'est-ce que la journalisation (logging) apporte en termes de sécurité ?",
     "Sécurité", "normal",
     ["Chiffrement automatique des fichiers sensibles",
      "Enregistrement des événements pour audit et détection d'incidents",
      "Suppression sécurisée des fichiers obsolètes",
      "Sauvegarde automatique des données utilisateurs"], "b"),

    ("Quel type d'attaque exploite une entrée non validée pour exécuter des commandes système ?",
     "Sécurité", "difficile",
     ["SQL Injection", "Command Injection",
      "XSS Stored", "CSRF"], "b"),

    ("Qu'est-ce que le principe de défense en profondeur ?",
     "Sécurité", "difficile",
     ["Utiliser un seul pare-feu très puissant",
      "Multiplier les couches de sécurité indépendantes",
      "Chiffrer toutes les communications réseau",
      "Désactiver tous les services non utilisés"], "b"),

    # ───── SYSTÈME (25) ─────
    ("Qu'est-ce qu'un processus zombie sous Linux ?",
     "Système", "difficile",
     ["Processus en attente de ressources CPU",
      "Processus terminé dont l'entrée reste dans la table des processus",
      "Processus infecté par un malware",
      "Processus en boucle infinie consommant du CPU"], "b"),

    ("Quelle commande liste les processus en cours d'exécution sous Linux ?",
     "Système", "facile",
     ["ls -la", "grep -r", "ps aux", "kill -9"], "c"),

    ("Qu'est-ce qu'un inode dans un système de fichiers Unix ?",
     "Système", "difficile",
     ["Le contenu binaire d'un fichier",
      "Le nom affiché d'un fichier dans un répertoire",
      "Structure contenant les métadonnées d'un fichier (permissions, taille…)",
      "Le répertoire racine du système"], "c"),

    ("Quelle commande modifie les permissions d'un fichier sous Linux ?",
     "Système", "facile",
     ["chown", "chmod", "chgrp", "ls -l"], "b"),

    ("Qu'est-ce que le swap sous Linux ?",
     "Système", "normal",
     ["Type de processeur virtuel",
      "Espace disque utilisé comme extension de la RAM",
      "Partition de démarrage du système",
      "Système de fichiers journalisé"], "b"),

    ("Qu'est-ce qu'un daemon (démon) sous Unix/Linux ?",
     "Système", "normal",
     ["Interface utilisateur graphique du système",
      "Programme s'exécutant en arrière-plan sans interface",
      "Type de virus système persistant",
      "Commande système d'administration"], "b"),

    ("Que signifie la permission '7' en notation octale Unix ?",
     "Système", "normal",
     ["Lecture seule (r--)",
      "Lecture et écriture (rw-)",
      "Lecture, écriture et exécution (rwx)",
      "Exécution seule (--x)"], "c"),

    ("Qu'est-ce que la mémoire virtuelle ?",
     "Système", "normal",
     ["RAM physique supplémentaire installée",
      "Extension de la RAM utilisant l'espace disque",
      "Cache du processeur (L1/L2/L3)",
      "Registres internes du CPU"], "b"),

    ("Quelle commande affiche l'utilisation de l'espace disque (partitions) sous Linux ?",
     "Système", "facile",
     ["du -sh", "ls -lh", "df -h", "fdisk -l"], "c"),

    ("Qu'est-ce qu'un thread ?",
     "Système", "normal",
     ["Processus totalement indépendant avec son propre espace mémoire",
      "Unité d'exécution légère partageant la mémoire d'un processus",
      "Instruction élémentaire exécutée par le CPU",
      "Fichier temporaire du système"], "b"),

    ("Que signifie POSIX ?",
     "Système", "difficile",
     ["Portable Open Source Interface for X systems",
      "Portable Operating System Interface",
      "Protocol Open System Interface eXtended",
      "Parallel Operating System Interface eXtended"], "b"),

    ("Qu'est-ce que le PID d'un processus ?",
     "Système", "facile",
     ["La priorité d'ordonnancement du processus",
      "L'adresse mémoire principale du processus",
      "L'identifiant unique numérique du processus",
      "La taille en mémoire du processus"], "c"),

    ("Qu'est-ce que le shell ?",
     "Système", "facile",
     ["Interface graphique du bureau Linux",
      "Interface de ligne de commande pour interagir avec le noyau",
      "Le noyau (kernel) du système d'exploitation",
      "Gestionnaire de fichiers graphique"], "b"),

    ("Qu'est-ce que cron sous Linux ?",
     "Système", "normal",
     ["Éditeur de texte en ligne de commande",
      "Planificateur de tâches automatiques récurrentes",
      "Gestionnaire de paquets Debian",
      "Serveur web léger"], "b"),

    ("Qu'est-ce qu'un lien symbolique (symlink) ?",
     "Système", "normal",
     ["Copie physique complète d'un fichier",
      "Raccourci pointant vers un fichier ou répertoire",
      "Fichier compressé en archive",
      "Connexion réseau persistante"], "b"),

    ("Quel fichier Linux contient les informations des comptes utilisateurs ?",
     "Système", "normal",
     ["/etc/shadow (mots de passe chiffrés)",
      "/etc/passwd (informations des comptes)",
      "/etc/network/interfaces (configuration réseau)",
      "/etc/services (liste des services réseau)"], "b"),

    ("Qu'est-ce que le kernel (noyau) d'un système d'exploitation ?",
     "Système", "normal",
     ["L'interface graphique de l'utilisateur",
      "Le gestionnaire de fichiers système",
      "La partie centrale gérant le matériel et les ressources",
      "L'interpréteur de commandes shell"], "c"),

    ("Quelle commande envoie un signal à un processus sous Linux ?",
     "Système", "facile",
     ["stop", "kill", "end", "terminate"], "b"),

    ("Qu'est-ce qu'un hyperviseur ?",
     "Système", "difficile",
     ["Type de processeur multi-cœurs",
      "Logiciel permettant de créer et gérer des machines virtuelles",
      "Protocole réseau de virtualisation",
      "Système de fichiers pour les conteneurs"], "b"),

    ("Qu'est-ce que systemd ?",
     "Système", "difficile",
     ["Éditeur de fichiers de configuration Linux",
      "Système d'initialisation et gestionnaire de services Linux moderne",
      "Gestionnaire de paquets universel",
      "Système de fichiers journalisé ext4"], "b"),

    ("Qu'est-ce qu'une variable d'environnement ?",
     "Système", "normal",
     ["Variable locale à une fonction du programme",
      "Variable globale Python accessible dans tout le module",
      "Variable accessible par les processus dans leur environnement d'exécution",
      "Variable de configuration d'une interface réseau"], "c"),

    ("Que fait la commande 'top' sous Linux ?",
     "Système", "facile",
     ["Affiche le haut d'un fichier texte",
      "Compresse les fichiers en archive tar",
      "Affiche en temps réel les processus et l'utilisation des ressources",
      "Modifie la priorité d'un processus"], "c"),

    ("Qu'est-ce que le principe de Copy-on-Write (CoW) ?",
     "Système", "difficile",
     ["Copier un fichier à chaque écriture pour l'historique",
      "Ne copier les données partagées qu'au moment d'une modification",
      "Écrire systématiquement deux copies de chaque fichier",
      "Protocole de synchronisation réseau en temps réel"], "b"),

    ("Quelle commande affiche l'utilisation détaillée de l'espace disque d'un dossier ?",
     "Système", "facile",
     ["df -h /dossier", "du -sh /dossier", "ls -la /dossier", "stat /dossier"], "b"),

    ("Qu'est-ce que le BIOS/UEFI ?",
     "Système", "facile",
     ["Système d'exploitation minimal",
      "Firmware initialisant le matériel avant le démarrage de l'OS",
      "Gestionnaire de démarrage Linux",
      "Interface graphique de configuration réseau"], "b"),

    # ───── PROGRAMMATION (25) ─────
    ("Qu'est-ce que la récursivité en programmation ?",
     "Programmation", "facile",
     ["Une boucle infinie sans condition d'arrêt",
      "Une fonction qui s'appelle elle-même avec un cas de base",
      "Un mécanisme d'héritage de classes",
      "La capacité d'un objet à prendre plusieurs formes"], "b"),

    ("Qu'est-ce qu'une classe abstraite en POO ?",
     "Programmation", "normal",
     ["Classe sans aucune méthode définie",
      "Classe ne pouvant pas être instanciée directement",
      "Classe avec un seul attribut public",
      "Classe héritant de toutes les autres classes"], "b"),

    ("Quelle est la complexité temporelle moyenne de l'algorithme quicksort ?",
     "Programmation", "difficile",
     ["O(n)", "O(n²)", "O(n log n)", "O(log n)"], "c"),

    ("Qu'est-ce que le polymorphisme en POO ?",
     "Programmation", "normal",
     ["Mécanisme permettant l'héritage multiple",
      "Capacité d'objets de types différents à répondre à la même interface",
      "Principe d'encapsulation des données privées",
      "Surcharge des opérateurs arithmétiques"], "b"),

    ("Qu'est-ce qu'une exception en programmation ?",
     "Programmation", "facile",
     ["Erreur fatale non gérable provoquant un crash",
      "Événement anormal interrompant le flux normal d'exécution",
      "Boucle infinie détectée à l'exécution",
      "Variable non initialisée utilisée en lecture"], "b"),

    ("Que signifie SOLID en conception logicielle orientée objet ?",
     "Programmation", "difficile",
     ["Cinq langages de programmation recommandés",
      "Cinq principes de conception orientée objet (SRP, OCP, LSP, ISP, DIP)",
      "Acronyme de sécurité applicative",
      "Méthode agile de gestion de projet"], "b"),

    ("Qu'est-ce qu'un design pattern (patron de conception) ?",
     "Programmation", "normal",
     ["Modèle de base de données normalisé",
      "Bibliothèque standard de fonctions réutilisables",
      "Solution générique et réutilisable à un problème récurrent de conception",
      "Standard de documentation de code"], "c"),

    ("Qu'est-ce que Git ?",
     "Programmation", "facile",
     ["Environnement de développement intégré (IDE)",
      "Langage de script pour l'automatisation",
      "Système de contrôle de version distribué",
      "Serveur web pour applications Python"], "c"),

    ("Qu'est-ce que la complexité O(1) ?",
     "Programmation", "normal",
     ["Complexité linéaire proportionnelle à la taille de l'entrée",
      "Complexité quadratique très lente",
      "Temps d'exécution constant indépendant de la taille de l'entrée",
      "Complexité logarithmique efficace"], "c"),

    ("Qu'est-ce qu'une liste chaînée ?",
     "Programmation", "normal",
     ["Tableau de taille fixe en mémoire contiguë",
      "Arbre binaire de recherche équilibré",
      "Structure de données où chaque nœud pointe vers le suivant",
      "File d'attente circulaire en mémoire"], "c"),

    ("Qu'est-ce que le principe DRY ?",
     "Programmation", "facile",
     ["Debug Rapidly and Yield results",
      "Don't Repeat Yourself – éviter la duplication de code",
      "Design Reusable Yet simple modules",
      "Dynamic Runtime Yielding optimization"], "b"),

    ("Qu'est-ce qu'une fonction lambda ?",
     "Programmation", "normal",
     ["Fonction récursive sans nom",
      "Fonction sans aucun paramètre",
      "Fonction anonyme définie en une seule expression",
      "Fonction asynchrone retournant une promesse"], "c"),

    ("Qu'est-ce que TDD (Test-Driven Development) ?",
     "Programmation", "normal",
     ["Tester l'application uniquement après le déploiement en production",
      "Écrire les tests unitaires avant d'écrire le code fonctionnel",
      "Tester exclusivement l'interface utilisateur avec Selenium",
      "Développer sans tests pour accélérer la livraison"], "b"),

    ("Qu'est-ce qu'une pile (stack) comme structure de données ?",
     "Programmation", "facile",
     ["Structure FIFO – premier entré, premier sorti",
      "Liste chaînée circulaire bidirectionnelle",
      "Structure LIFO – dernier entré, premier sorti",
      "Tableau associatif clé-valeur"], "c"),

    ("Qu'est-ce qu'une file (queue) comme structure de données ?",
     "Programmation", "facile",
     ["Structure LIFO – dernier entré, premier sorti",
      "Pile inversée à double entrée",
      "Structure FIFO – premier entré, premier sorti",
      "Arbre binaire de recherche"], "c"),

    ("Qu'est-ce que l'encapsulation en POO ?",
     "Programmation", "normal",
     ["Mécanisme d'héritage multiple entre classes",
      "Principe polymorphique multi-forme",
      "Regroupement des données et méthodes avec contrôle d'accès",
      "Création automatique d'instances d'objets"], "c"),

    ("Qu'est-ce que JSON ?",
     "Programmation", "facile",
     ["Langage de programmation orienté objet",
      "JavaScript Object Notation – format léger d'échange de données",
      "Base de données orientée document",
      "Protocole réseau de communication binaire"], "b"),

    ("Qu'est-ce qu'un algorithme de recherche binaire ?",
     "Programmation", "normal",
     ["Recherche séquentielle parcourant chaque élément",
      "Recherche dans un tableau trié en divisant l'espace de recherche par deux",
      "Algorithme de tri rapide récursif",
      "Recherche en profondeur dans un arbre"], "b"),

    ("Qu'est-ce que la programmation fonctionnelle ?",
     "Programmation", "normal",
     ["Paradigme où tout est organisé en classes et objets",
      "Programmation sans utiliser de fonctions",
      "Paradigme traitant le calcul comme l'évaluation de fonctions mathématiques pures",
      "Programmation par événements asynchrones"], "c"),

    ("Qu'est-ce que l'héritage en POO ?",
     "Programmation", "normal",
     ["Copie complète d'un objet en mémoire",
      "Mécanisme permettant à une classe d'hériter attributs et méthodes d'une autre",
      "Partage de données entre threads parallèles",
      "Principe d'encapsulation des données"], "b"),

    ("Qu'est-ce qu'une méthode statique (static) ?",
     "Programmation", "normal",
     ["Méthode accessible uniquement depuis la classe dérivée",
      "Méthode héritée automatiquement par toutes les sous-classes",
      "Méthode appartenant à la classe et non à une instance spécifique",
      "Méthode abstraite devant être implémentée"], "c"),

    ("Qu'est-ce que la surcharge d'opérateurs ?",
     "Programmation", "difficile",
     ["Création de nouveaux opérateurs mathématiques",
      "Redéfinition du comportement d'un opérateur pour un type personnalisé",
      "Conversion automatique de types primitifs",
      "Polymorphisme paramétrique avec génériques"], "b"),

    ("Quelle est la complexité de l'algorithme de tri par insertion dans le pire cas ?",
     "Programmation", "difficile",
     ["O(n log n)", "O(n²)", "O(n)", "O(log n)"], "b"),

    ("Qu'est-ce qu'une API REST ?",
     "Programmation", "normal",
     ["Base de données relationnelle exposée en réseau",
      "Interface de programmation utilisant les méthodes HTTP (GET, POST, PUT, DELETE)",
      "Framework frontend JavaScript moderne",
      "Protocole de communication binaire performant"], "b"),

    ("Qu'est-ce qu'un pointeur en langage C ?",
     "Programmation", "difficile",
     ["Variable globale accessible partout dans le programme",
      "Variable contenant l'adresse mémoire d'une autre variable",
      "Constante numérique définie à la compilation",
      "Type spécial de tableau à taille variable"], "b"),

    # ───── BASE DE DONNÉES (25) ─────
    ("Que signifie SQL ?",
     "Base de données", "facile",
     ["Simple Query Language",
      "Structured Query Language",
      "Sequential Query Language",
      "System Query Language"], "b"),

    ("Quelle est la différence entre clé primaire et clé étrangère ?",
     "Base de données", "normal",
     ["Aucune différence fonctionnelle entre les deux",
      "La clé primaire identifie chaque ligne de façon unique ; la clé étrangère référence une autre table",
      "La clé primaire peut contenir des valeurs NULL",
      "La clé étrangère doit toujours être unique dans sa table"], "b"),

    ("Qu'est-ce que la normalisation d'une base de données ?",
     "Base de données", "normal",
     ["Chiffrement des données sensibles stockées",
      "Processus d'organisation réduisant la redondance et les anomalies",
      "Optimisation automatique des requêtes SQL",
      "Création d'index sur toutes les colonnes"], "b"),

    ("Quelle commande SQL insère des données dans une table ?",
     "Base de données", "facile",
     ["ADD INTO table VALUES",
      "INSERT INTO table VALUES",
      "PUT INTO table VALUES",
      "CREATE INTO table VALUES"], "b"),

    ("Que signifie ACID pour les transactions ?",
     "Base de données", "difficile",
     ["Automatique, Cohérent, Intègre, Distribué",
      "Atomicité, Cohérence, Isolation, Durabilité",
      "Algorithme, Calcul, Indexation, Distribution",
      "Authentification, Confidentialité, Intégrité, Disponibilité"], "b"),

    ("Qu'est-ce qu'un index en base de données ?",
     "Base de données", "normal",
     ["Contrainte de clé étrangère",
      "Copie complète d'une table pour la redondance",
      "Structure de données optimisant la vitesse des recherches",
      "Type de contrainte d'intégrité référentielle"], "c"),

    ("Quelle clause SQL filtre les lignes d'un résultat ?",
     "Base de données", "facile",
     ["FILTER BY colonne", "HAVING condition",
      "WHERE condition", "GROUP BY colonne"], "c"),

    ("Qu'est-ce qu'une jointure (JOIN) SQL ?",
     "Base de données", "normal",
     ["Union de deux bases de données distinctes",
      "Combinaison de lignes de plusieurs tables selon une condition",
      "Copie physique d'une table dans une autre",
      "Tri des résultats par plusieurs colonnes"], "b"),

    ("Que fait SELECT DISTINCT en SQL ?",
     "Base de données", "normal",
     ["Sélectionne toutes les lignes sans exception",
      "Trie les résultats dans l'ordre croissant",
      "Retourne uniquement les valeurs distinctes sans doublons",
      "Filtre les valeurs NULL de la sélection"], "c"),

    ("Qu'est-ce qu'une vue (VIEW) en SQL ?",
     "Base de données", "normal",
     ["Copie physique et matérialisée d'une table",
      "Requête SQL sauvegardée présentée comme une table virtuelle",
      "Index composite sur plusieurs colonnes",
      "Procédure stockée sans paramètres"], "b"),

    ("Quelle est la différence entre DELETE et TRUNCATE en SQL ?",
     "Base de données", "difficile",
     ["Aucune différence fonctionnelle entre les deux",
      "DELETE supprime ligne par ligne (annulable) ; TRUNCATE vide la table entière (plus rapide)",
      "TRUNCATE peut utiliser une clause WHERE pour filtrer",
      "DELETE ne peut pas être annulé par un ROLLBACK"], "b"),

    ("Qu'est-ce que NoSQL ?",
     "Base de données", "normal",
     ["Extension SQL pour les requêtes avancées",
      "Famille de bases de données non relationnelles",
      "Protocole réseau de communication avec les BDD",
      "Outil de chiffrement des bases de données"], "b"),

    ("Quelle commande SQL modifie la structure d'une table existante ?",
     "Base de données", "normal",
     ["MODIFY TABLE", "CHANGE TABLE", "UPDATE TABLE", "ALTER TABLE"], "d"),

    ("Qu'est-ce qu'une procédure stockée ?",
     "Base de données", "difficile",
     ["Vue de base de données en lecture seule",
      "Programme SQL stocké dans la base de données et réutilisable",
      "Type d'index partiel sur une colonne",
      "Contrainte d'intégrité référentielle avancée"], "b"),

    ("Que fait la clause GROUP BY en SQL ?",
     "Base de données", "normal",
     ["Trie les résultats finaux dans un ordre précis",
      "Filtre les données avant agrégation",
      "Regroupe les lignes selon une ou plusieurs colonnes pour les agréger",
      "Effectue une jointure entre plusieurs tables"], "c"),

    ("Qu'est-ce qu'un ORM ?",
     "Base de données", "normal",
     ["Outil de sauvegarde et restauration de base de données",
      "Object-Relational Mapping : fait correspondre objets et tables relationnelles",
      "Optimiseur automatique de requêtes SQL",
      "Protocole de réplication entre serveurs"], "b"),

    ("Que fait la fonction SQL COUNT() ?",
     "Base de données", "facile",
     ["Additionne les valeurs numériques d'une colonne",
      "Retourne la valeur maximale d'une colonne",
      "Compte le nombre de lignes ou de valeurs non nulles",
      "Calcule la moyenne arithmétique d'une colonne"], "c"),

    ("Qu'est-ce qu'une contrainte UNIQUE en SQL ?",
     "Base de données", "normal",
     ["Rend la colonne obligatoire (non NULL)",
      "Garantit que les valeurs d'une colonne sont toutes distinctes",
      "Crée automatiquement un index de hachage",
      "Définit une clé primaire composite"], "b"),

    ("Que signifie DML en SQL ?",
     "Base de données", "difficile",
     ["Data Modeling Language pour la conception",
      "Data Manipulation Language : SELECT, INSERT, UPDATE, DELETE",
      "Database Management Language pour l'administration",
      "Data Migration Language pour les imports"], "b"),

    ("Qu'est-ce qu'un trigger (déclencheur) SQL ?",
     "Base de données", "difficile",
     ["Type d'index déclenché automatiquement à la création",
      "Action SQL automatique déclenchée par un événement INSERT/UPDATE/DELETE",
      "Procédure manuelle exécutée par l'administrateur",
      "Vue spéciale avec mise à jour automatique"], "b"),

    ("Qu'est-ce que la 3NF (Troisième Forme Normale) ?",
     "Base de données", "difficile",
     ["Suppression de tous les doublons dans les tables",
      "Création de clés composites sur toutes les tables",
      "Élimination des dépendances transitives entre attributs non-clés",
      "Optimisation des jointures par dénormalisation"], "c"),

    ("Qu'est-ce que la réplication de base de données ?",
     "Base de données", "difficile",
     ["Chiffrement des données sur le disque",
      "Copie des données sur plusieurs serveurs pour la redondance et disponibilité",
      "Optimisation automatique des requêtes lentes",
      "Normalisation de toutes les tables de la base"], "b"),

    ("Qu'est-ce qu'une transaction en base de données ?",
     "Base de données", "normal",
     ["Type de requête SELECT complexe avec plusieurs jointures",
      "Ensemble d'opérations formant une unité atomique (tout ou rien)",
      "Procédure stockée paramétrée réutilisable",
      "Vue matérialisée rafraîchie périodiquement"], "b"),

    ("Quel est l'opérateur SQL pour combiner les résultats de deux requêtes sans doublons ?",
     "Base de données", "normal",
     ["JOIN", "UNION", "INTERSECT", "MERGE"], "b"),

    ("Qu'est-ce que le sharding en bases de données ?",
     "Base de données", "difficile",
     ["Chiffrement partitionné des colonnes sensibles",
      "Distribution horizontale des données sur plusieurs serveurs",
      "Technique de compression des index",
      "Méthode de backup incrémental nocturne"], "b"),
]


def seed():
    with app.app_context():
        print("Réinitialisation de la base de données...")
        db.drop_all()
        db.create_all()

        # ── Admin (A2F désactivée pour faciliter les tests) ──
        admin = User(
            username='admin',
            email='admin@qcm-lpassr.fr',
            password_hash=bcrypt.generate_password_hash('Admin1234!').decode('utf-8'),
            role='admin',
            is_active=True,
            totp_secret=pyotp.random_base32(),
            totp_enabled=False
        )
        db.session.add(admin)

        # ── Étudiant de test ──
        student = User(
            username='etudiant',
            email='etudiant@qcm-lpassr.fr',
            password_hash=bcrypt.generate_password_hash('Etudiant1234!').decode('utf-8'),
            role='student',
            is_active=True,
            totp_secret=pyotp.random_base32(),
            totp_enabled=False
        )
        db.session.add(student)

        print(f"Création de {len(QUESTIONS)} questions...")
        for q_text, category, difficulty, options, correct_letter in QUESTIONS:
            q = Question(text=q_text, category=category, difficulty=difficulty)
            db.session.add(q)
            db.session.flush()

            letter_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3}
            correct_idx = letter_map[correct_letter]

            for i, opt_text in enumerate(options):
                opt = Option(
                    question_id=q.id,
                    text=opt_text,
                    is_correct=(i == correct_idx),
                    order=i
                )
                db.session.add(opt)

        # ── Quiz planifié d'exemple (disponible 72h) ──
        now = datetime.utcnow()
        quiz_demo = ScheduledQuiz(
            name='Quiz Démo – Réseaux & Sécurité',
            description='Quiz d\'exemple couvrant les réseaux et la sécurité informatique.',
            start_time=now,
            end_time=now + timedelta(hours=72),
            question_count=10,
            category_filter=None,
            difficulty_filter=None,
            is_active=True
        )
        db.session.add(quiz_demo)

        db.session.commit()

        total = Question.query.count()
        print(f"\nBase de données initialisée avec succès !")
        print(f"  Questions  : {total}")
        print(f"  Quiz démo  : actif 72h")
        print(f"  Comptes créés :")
        print(f"    Admin    → username: admin       / password: Admin1234!")
        print(f"    Étudiant → username: etudiant    / password: Etudiant1234!")
        print(f"\n  Note : l'A2F est désactivée sur ces comptes de test.")
        print(f"         Les nouveaux comptes créés via /register devront la configurer.")
        print(f"\nDémarrez l'application avec : python app.py")


if __name__ == '__main__':
    seed()
