import os
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Patate est vivant.")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def lancer_port_factice():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), DummyHandler)
    server.serve_forever()

threading.Thread(target=lancer_port_factice).start()



import discord
import random
import datetime
from datetime import datetime, timedelta
import json
import os
import requests
from dotenv import load_dotenv

import asyncio

async def keep_alive():
    while True:
        print("Patate respire.")
        await asyncio.sleep(300)

# -------- CONFIGURATION --------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

# ------ BADGES -----------------

ROLES_JEUX = {
    "pendu": [
        {"min": 1, "max": 20, "role": "Humain Faible"},
        {"min": 21, "max": 50, "role": "Petit deviendra Grand"},
        {"min": 51, "max": 100, "role": "Légende Vivante"},
        {"min": 101, "max": 999, "role": "Machine de guerre"},
    ],
    "bac": [
        {"min": 1, "max": 20, "role": "Connait son alphabet"},
        {"min": 21, "max": 50, "role": "Maîtrise le français"},
        {"min": 51, "max": 100, "role": "Incroyablement bon !"},
        {"min": 101, "max": 999, "role": "Le Dictionnaire, c'est toi ?"},
    ],
    "devine": [
        {"min": 1, "max": 20, "role": "Essayes encore !"},
        {"min": 21, "max": 50, "role": "Iconique"},
        {"min": 51, "max": 100, "role": "Excellence !"},
        {"min": 101, "max": 999, "role": "T'es dans mon cerveau, avoue ?"},
    ],
    "croquette": [
        {"min": 1, "max": 20, "role": "Radin !"},
        {"min": 21, "max": 50, "role": "Ok, je t'aime bien !"},
        {"min": 51, "max": 100, "role": "Merci pour ta générosité"},
        {"min": 101, "max": 999, "role": "Tu veux me bouffer, c'est ça ?"},
    ],
}

# Remplace ce chemin si tu déplaces le fichier image
BADGE_IMAGE_PATH = "chaGG.png"

async def update_role(message, jeu, score):
    user = message.author
    guild = message.guild

    if jeu not in ROLES_JEUX:
        return

    palier = next((r for r in ROLES_JEUX[jeu] if r["min"] <= score <= r["max"]), None)
    if not palier:
        return

    role_name = palier["role"]
    role = discord.utils.get(guild.roles, name=role_name)
    if not role:
        await message.channel.send(f"⚠️ Rôle `{role_name}` introuvable.")
        return

    if role in user.roles:
        return

    autres_roles = [discord.utils.get(guild.roles, name=r["role"]) for r in ROLES_JEUX[jeu] if r["role"] != role_name]
    for r in autres_roles:
        if r and r in user.roles:
            await user.remove_roles(r)

    await user.add_roles(role)

    # Envoi du DM avec image
    try:
        with open(BADGE_IMAGE_PATH, "rb") as f:
            image_file = discord.File(f, filename="badge.png")
            msg = (
                f"Heyyy {user.mention} !\n\n"
                f"Tu as mon respect pour 5min, tu as réussi à débloquer ce badge : **{role_name}** !\n\n"
                f"Félicitations l'humain(e) !\n\n"
                f"Mais... Vas-tu réussir à atteindre le niveau supérieur ?"
            )
            await user.send(content=msg, file=image_file)
    except Exception as e:
        await message.channel.send(f"⚠️ Impossible d'envoyer un DM à {user.mention}.")
        print(f"Erreur DM : {e}")


# --------- JEUX ---------------

parties_en_cours = {} # stock le chiffre a deviné
scores = {} # stock les voictoires / défaites

SCORES_FILE = "patate_scores.json"

def charger_scores():
    if os.path.exists(SCORES_FILE):
        with open(SCORES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def sauvegarder_scores():
    with open(SCORES_FILE, "w", encoding="utf-8") as f:
        json.dump(scores, f, ensure_ascii=False, indent=4)

scores = charger_scores()

pendu_en_cours = {}

with open("pendu_data.json", "r", encoding="utf-8") as f:
    mots_pendu = json.load(f)["mots"]

bac_en_cours = {}  # stocke la lettre en cours pour chaque joueur dans le jeu du baccalauréat

# ------- UNO - gestion des parties --------

parties_uno = {}

def initialiser_partie_uno(channel_id):
    parties_uno[channel_id] = {
        "joueurs": [],
        "en_cours": False
    }

def rejoindre_partie_uno(channel_id, user):
    if channel_id not in parties_uno:
        return "❌ Aucune partie en cours. Tape `!uno start` d'abord."
    if parties_uno[channel_id]["en_cours"]:
        return "🚫 La partie a déjà commencé !"
    if user.id in [j.id for j in parties_uno[channel_id]["joueurs"]]:
        return "😼 Tu es déjà dans la partie."
    if len(parties_uno[channel_id]["joueurs"]) >= 4:
        return "🃏 La partie est pleine (4 joueurs max)."
    parties_uno[channel_id]["joueurs"].append(user)
    return f"✅ {user.display_name} a rejoint la partie UNO !"

def lancer_partie_uno(channel_id):
    if channel_id not in parties_uno:
        return "❌ Aucune partie UNO ici. Tape `!uno start` pour en créer une."
    joueurs = parties_uno[channel_id]["joueurs"]
    if len(joueurs) < 2:
        return "🙄 Faut être au moins 2 pour jouer, humain."
    parties_uno[channel_id]["en_cours"] = True
    noms = ", ".join([j.display_name for j in joueurs])
    return f"🎉 La partie commence avec : {noms}\n(Patate distribue les cartes... en mode passif-agressif.)"

def creer_deck_uno():
    couleurs = ["rouge", "jaune", "vert", "bleu"]
    valeurs = [str(n) for n in range(0, 10)] + ["skip", "+2", "reverse"]
    deck = []

    for couleur in couleurs:
        for val in valeurs:
            if val == "0":
                deck.append((couleur, val))
            else:
                deck.extend([(couleur, val)] * 2)

    specials = [("noir", "+4")] * 4 + [("noir", "joker")] * 4
    deck.extend(specials)

    random.shuffle(deck)
    return deck

def distribuer_mains(joueurs, deck):
    mains = {}
    for joueur in joueurs:
        mains[joueur.id] = [deck.pop() for _ in range(7)]
    return mains, deck

def tirer_premiere_carte(deck):
    while deck:
        carte = deck.pop()
        if carte[0] != "noir":
            return carte, deck
    return None, deck  # Si jamais il n'y avait que des cartes noires (improbable)

def carte_valide(carte, carte_visible):
    return (
        carte[0] == carte_visible[0] or  # même couleur
        carte[1] == carte_visible[1] or  # même valeur
        carte[0] == "noir"               # carte spéciale
    )

def jouer_carte_avec_noir(channel_id, joueur_id, couleur, valeur, couleur_choisie=None):
    if channel_id not in parties_uno:
        return "❌ Aucune partie UNO ici."

    partie = parties_uno[channel_id]
    if not partie["en_cours"]:
        return "🚫 La partie n'a pas encore commencé."

    if joueur_id != partie["joueur_actuel"]:
        return "🕐 Ce n’est pas ton tour, bipède impatient."

    main = partie["mains"].get(joueur_id, [])
    carte = (couleur, valeur)

    if carte not in main:
        return f"🃏 Tu n’as pas cette carte : {couleur} {valeur}."

    if couleur == "noir" and not couleur_choisie:
        return "🎨 Tu dois choisir une couleur à jouer avec cette carte noire ! (ex: !play noir +4 rouge)"

    # Jouer la carte
    main.remove(carte)
    carte_visible = (couleur_choisie, valeur) if couleur == "noir" else carte
    partie["carte_visible"] = carte_visible
    victoire = verifier_victoire(channel_id, joueur_id)
    if victoire:
        return victoire

    joueurs = partie["joueurs"]
    index = next((i for i, j in enumerate(joueurs) if j.id == joueur_id), 0)
    joueur_suivant = joueurs[(index + 1) % len(joueurs)]

    message = f"✅ Carte jouée : {carte[0]} {carte[1]}\n🎨 Couleur choisie : {carte_visible[0]}\n"

    if valeur == "+4":
        for _ in range(4):
            partie["mains"][joueur_suivant.id].append(partie["deck"].pop())
        message += "➕ Le joueur suivant pioche 4 cartes !\n"

    partie["joueur_actuel"] = joueur_suivant.id
    message += f"🕐 C’est à **{joueur_suivant.display_name}** de jouer."

    return message

def verifier_victoire(channel_id, joueur_id):
    if channel_id not in parties_uno:
        return None  # Pas de partie

    main = parties_uno[channel_id]["mains"].get(joueur_id, [])
    if len(main) == 0:
        parties_uno[channel_id]["en_cours"] = False
        return f"🏆 **Victoire !** <@{joueur_id}> n’a plus de cartes.\n🎉 La partie est terminée. Patate te juge... mais t’applaudit quand même."
    
    return None



def jouer_carte_avancee(channel_id, joueur_id, couleur, valeur):
    if channel_id not in parties_uno:
        return "❌ Aucune partie UNO ici."

    partie = parties_uno[channel_id]

    if not partie["en_cours"]:
        return "🚫 La partie n'a pas encore commencé."

    if joueur_id != partie["joueur_actuel"]:
        return "🕐 Ce n’est pas ton tour, bipède impatient."

    main = partie["mains"].get(joueur_id, [])
    carte = (couleur, valeur)

    if carte not in main:
        return f"🃏 Tu n’as pas cette carte : {couleur} {valeur}."

    if not carte_valide(carte, partie["carte_visible"]):
        return f"🚫 Tu ne peux pas jouer cette carte sur {partie['carte_visible'][0]} {partie['carte_visible'][1]}." 

    # Jouer la carte
    main.remove(carte)
    partie["carte_visible"] = carte
    victoire = verifier_victoire(channel_id, joueur_id)
    if victoire:
        return victoire

    # Avancer au joueur suivant
    joueurs = partie["joueurs"]
    index = next((i for i, j in enumerate(joueurs) if j.id == joueur_id), 0)
    if valeur == "reverse":
        joueurs.reverse()
        index = len(joueurs) - 1 - index

    if valeur == "skip":
        index = (index + 1) % len(joueurs)

    joueur_suivant = joueurs[(index + 1) % len(joueurs)]

    if valeur == "+2":
        for _ in range(2):
            partie["mains"][joueur_suivant.id].append(partie["deck"].pop())
            message += "➕ Le joueur suivant pioche 2 cartes !\n"


    partie["joueur_actuel"] = joueur_suivant.id

    partie["joueur_actuel"] = joueur_suivant.id
    return f"✅ Carte jouée : {couleur} {valeur}\n📤 Nouvelle carte visible : {couleur} {valeur}\n🕐 C’est à **{joueur_suivant.display_name}** de jouer."

def quitter_partie_uno(channel_id, joueur_id):
    if channel_id not in parties_uno:
        return "❌ Aucune partie UNO ici."

    partie = parties_uno[channel_id]
    joueurs = partie["joueurs"]

    joueurs = [j for j in joueurs if j.id != joueur_id]
    partie["joueurs"] = joueurs

    if "mains" in partie:
        partie["mains"].pop(joueur_id, None)

    if len(joueurs) < 2 and partie.get("en_cours"):
        partie["en_cours"] = False
        return f"🚪 Le joueur <@{joueur_id}> a quitté la partie. Moins de 2 joueurs restants. La partie est terminée."

    return f"🚪 Le joueur <@{joueur_id}> a quitté la partie UNO."


def reset_partie_uno(channel_id):
    if channel_id in parties_uno:
        del parties_uno[channel_id]
    return "♻️ Partie UNO réinitialisée. Tape `!uno start` pour en créer une nouvelle."


def uno_piocher(channel_id, joueur_id):
    if channel_id not in parties_uno:
        return "❌ Aucune partie UNO ici."

    partie = parties_uno[channel_id]

    if not partie["en_cours"]:
        return "🚫 La partie n'a pas encore commencé."

    if joueur_id != partie["joueur_actuel"]:
        return "🕐 Ce n’est pas ton tour, bipède impatient."

    deck = partie.get("deck", [])
    if not deck:
        return "😿 Le paquet est vide. Patate panique."

    carte = deck.pop()
    partie["mains"][joueur_id].append(carte)

    # Avancer au joueur suivant
    joueurs = partie["joueurs"]
    index = next((i for i, j in enumerate(joueurs) if j.id == joueur_id), 0)
    joueur_suivant = joueurs[(index + 1) % len(joueurs)]
    partie["joueur_actuel"] = joueur_suivant.id

    return f"📥 Tu as pioché : {carte[0]} {carte[1]}\n🕐 C’est à **{joueur_suivant.display_name}** de jouer."

async def uno_main(message):
    channel_id = message.channel.id
    user_id = message.author.id

    if channel_id not in parties_uno:
        await message.channel.send("❌ Aucune partie UNO ici.")
        return

    partie = parties_uno[channel_id]
    if user_id not in partie["mains"]:
        await message.channel.send("🚫 Tu ne participes pas à cette partie.")
        return

    main = partie["mains"][user_id]
    cartes_txt = ", ".join([f"{c[0]} {c[1]}" for c in main])
    try:
        await message.author.send(f"🃏 **Voici ta main actuelle :**\n{cartes_txt}")
    except:
        await message.channel.send("❌ Impossible de t’envoyer ta main (DM désactivés ?)")




# ---------- DONNE A MANGER AU CHAT ----------------

# Fichier de sauvegarde
PATAFILE = "patate_data.json"

def charger_donnees_patate():
    donnees_defaut = {
        "poids": 50,
        "dernier_repas": datetime.now().isoformat(),
        "donateurs": {}
    }

    if os.path.exists(PATAFILE):
        with open(PATAFILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}

        # Merge données existantes + défaut
        for cle, valeur in donnees_defaut.items():
            if cle not in data:
                data[cle] = valeur

        return data

    return donnees_defaut

def sauvegarder_donnees_patate(data):
    with open(PATAFILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def commande_croquette(user_id):
    data = charger_donnees_patate()
    now = datetime.now()
    now_str = now.isoformat()

    # Patate maigrit s'il n'a pas été nourri depuis 24h
    if data.get("dernier_repas"):
        dernier_repas = datetime.fromisoformat(data["dernier_repas"])
        if now - dernier_repas > timedelta(hours=24):
            data["poids"] = max(0, data["poids"] - 2)

    # Vérif du quota par utilisateur
    donateurs = data.get("donateurs", {})
    user_logs = donateurs.get(user_id, [])
    recent_dons = [datetime.fromisoformat(d) for d in user_logs if now - datetime.fromisoformat(d) < timedelta(hours=12)]

    if len(recent_dons) >= 5:
        return f"🚫 Patate a assez mangé venant de toi pour aujourd'hui ! (5 croquettes max / 12h)"

    # Ajout de la croquette
    data["poids"] += 1
    recent_dons.append(now)
    donateurs[user_id] = [d.isoformat() for d in recent_dons]
    data["donateurs"] = donateurs
    data["dernier_repas"] = now_str

    sauvegarder_donnees_patate(data)

    # Réponse RP
    poids = data["poids"]
    if poids < 20:
        etat = "Un coup de vent et il s'envole... Nourrit le cette pauvre bête !"
    elif poids < 60:
        etat = "C'est un gros chat !"
    else:
        etat = "C'est plus simple de le faire rouler que de le porter !"

    return f"🍽️ Tu as donné une croquette à Patate.\n[Poids actuel : {poids}/100]\n{etat}"

def commande_etat():
    data = charger_donnees_patate()
    poids = data["poids"]

    if poids < 20:
        etat = "🥀 Patate est tout maigre... ses yeux plein d'amour demande des croquettes."
    elif poids < 60:
        etat = "😺 Patate est en forme. Il t’observe !"
    else:
        etat = "🐷 Patate déborde d'amour et ronfle en stéréo. Il vit sa meilleure vie."

    return f"📊 État de Patate :\nPoids actuel : {poids}/100\n{etat}"


# -------- LA CONNERIE DU JOUR FACON CLUEDO ------------

connerie_file_path = "patate_connerie.json"  # Ou adapte le chemin


armes = [
    "une chaussette humide", "une boule de poils radioactive", "un coup de patte bien mérité",
    "une plume de pigeon enragé", "un miaulement strident de 4h du mat", "une toupie possédée"
]

consequences = [
    "Le serveur n’a plus jamais été le même.",
    "Depuis, plus personne n’ose utiliser les emojis animés.",
    "Ça a déclenché un séisme de niveau 2 dans le vocal.",
    "Des miaulements hantent encore les logs de modération.",
    "Un admin a ragequit et s’est exilé.",
    "Le bot météo ne répond plus. Par peur."
]

def get_connerie_vraie(guild):
    today = datetime.now().date().isoformat()

    try:
        with open(connerie_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if data["date"] == today:
                return data["connerie"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass

    membres = [m for m in guild.members if not m.bot]
    victime = random.choice(membres).mention if membres else "@Quelqu’un"

    canaux_visibles = [
        c for c in guild.text_channels
        if c.permissions_for(guild.me).send_messages and not c.is_nsfw()
    ]
    lieu = random.choice(canaux_visibles).mention if canaux_visibles else "#quelque-part"

    arme = random.choice(armes)
    effet = random.choice(consequences)
    
    victime_membre = random.choice(membres)
    victime_id = victime_membre.id
    victime_mention = victime_membre.mention

    connerie = (
        f"📅 **Connerie du jour :**\n\n"
        f"Patate a attaqué {victime_mention} avec {arme} dans le channel {lieu}.\n"
        f"{effet}\n\n"
        f"🐾 *Demain, peut-être une autre victime...*"
    )

    
    json.dump({"date": today, "connerie": connerie, "victime_id": victime_id}, f, indent=4, ensure_ascii=False)

    with open(connerie_file_path, "w", encoding="utf-8") as f:
        json.dump({"date": today, "connerie": connerie}, f, indent=4, ensure_ascii=False)

    return connerie

def commande_pardon():
    return random.choice([
        "😾 Patate t’a vu... mais il ne te connaît pas.",
        "😼 Patate daigne te jeter un regard. C’est déjà beaucoup.",
        "🐾 Il ronronne... mais c’est peut-être parce qu’il a faim, pas grâce à toi.",
        "👑 Patate t’accorde son pardon royal... pour cette fois.",
        "🙀 Tu veux son pardon ? Il exige trois croquettes, un sacrifice et une offrande de thon.",
        "🐈‍⬛ Patate dort. Il te pardonnera peut-être demain. Ou jamais."
        ])

def commande_vengeance():
        return random.choice([
            "🪓 Tu lèves la main sur Patate ? Il lève la queue sur ta dignité.",
            "😾 Patate t’a vu. Il te suit maintenant. Même dans tes rêves.",
            "👁️ Tu as essayé. Tu as échoué. Patate t'appelle 'humain numéro 456'.",
            "💥 Patate te lance une boule de poils explosive. Elle explose dans ta poche.",
            "🐾 Tu veux te venger ? Patate a déjà changé le mot de passe du Wi-Fi.",
            "🎭 La vengeance est un plat qui se mange froid... mais Patate a vomi dedans."
        ])
def peut_se_venger(user_id):
    try:
        with open("patate_connerie.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("victime_id") == user_id
    except:
        return False

def get_badges_utilisateur(message):
    user = message.author
    roles_utilisateur = [r.name for r in user.roles]

    emoji_palier = {
        0: "🥉",
        1: "🥈",
        2: "🏅",
        3: "🏆"
    }

    badges = f"📛 **Tes Badges obtenus, humble bipède :**\n\n"

    for jeu, paliers in ROLES_JEUX.items():
        emoji_jeu = {
            "devine": "🔢",
            "pendu": "🔤",
            "bac": "🎓",
            "croquette": "🍽️"
        }.get(jeu, "🔹")
        badges += f"{emoji_jeu} {jeu.capitalize()} :\n"

        badge_trouvé = False
        for i, palier in enumerate(paliers):
            if palier["role"] in roles_utilisateur:
                badges += f"{emoji_palier.get(i, '🔹')} {palier['role']}\n"
                badge_trouvé = True
                break

        if not badge_trouvé:
            badges += "❌ Aucun badge pour ce jeu (encore...)\n"

        badges += "\n"

    return badges

# -------------- DISCORD ----------------------

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
client = discord.Client(intents=intents)


# Charger les répliques depuis un seul fichier JSON
with open("patate_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

repliques_commandes = data["commandes"]
repliques_humain = data["humain"]

@client.event
async def on_member_join(member):
    salon_bienvenue = client.get_channel(1364311094029451395)  # Remplace par l'ID de ton salon de bienvenue

    messages_bienvenue = [
        f"Bienvenue {member.mention} ! PatateBot t'observe... 👁️",
        f"Yo {member.name}, entre donc dans la folie de ce serveur.",
        f"{member.mention} vient d’arriver. PatateBot : 't’as intérêt à lire les règles'.",
        f"Bienvenue {member.name}, prépare-toi à juger ou être jugé.",
    ]

    presentation = (
        "👉 Ici, tu peux jouer avec `!jeux`, faire des bacs, des pendus, et discuter dans les bons salons.\n"
        "🎨 Si tu veux partager tes dessins, direction #nos-beaux-arts.\n"
        "📚 Pense à lire les règles pour éviter les coups de griffes."
    )

    await salon_bienvenue.send(random.choice(messages_bienvenue))
    await salon_bienvenue.send(presentation)


@client.event
async def on_ready():
    print(f"Patate est en ligne sous le nom {client.user} !")

    activites = [
        (discord.ActivityType.watching, "Mes humaines préférées !"),
        (discord.ActivityType.listening, "Tes conneries !"),
        (discord.ActivityType.playing, "Avec sa queue comme un débile"),
        (discord.ActivityType.watching, "Une mouche voler"),
        (discord.ActivityType.listening, "Le son du mépris"),
        (discord.ActivityType.playing, "Avec du plastique"),
        (discord.ActivityType.watching, "Matte par la fenêtre"),
        (discord.ActivityType.listening, "La pluie. Pas toi."),
        (discord.ActivityType.streaming, "Regarde le sacrifice d'un oiseau en direct"),
        (discord.ActivityType.streaming, "Regarde ma mini humaine dessinée son art"),
        (discord.ActivityType.streaming, "Regarde des chats qui dansent")
    ]

    type_act, nom = random.choice(activites)
    await client.change_presence(activity=discord.Activity(type=type_act, name=nom))

    client.loop.create_task(keep_alive())


@client.event
async def on_member_remove(member):
    salon_bienvenue = client.get_channel(1364311094029451395)  # Même salon que pour les arrivées

    messages_depart = [
        f"{member.name} a fui. Patate le soupçonnait déjà.",
        f"Adieu {member.name}. Moins de bipèdes, plus de croquettes.",
        f"{member.name} est parti... Patate ne le regrettera pas.",
    ]

    await salon_bienvenue.send(random.choice(messages_depart))

@client.event
async def on_message(message):
    if message.author == client.user:
        return
    content = message.content.lower().lstrip("!")

    # Commande !uno

    if content == "uno" and message.channel.id == 1363967793669738626:
        await message.channel.send(f"🗣️ {message.author.display_name} crie **UNO !**")
        return


    if content == "uno launch" and message.channel.id == 1363967793669738626:
        reponse = lancer_partie_uno(message.channel.id)
        await message.channel.send(reponse)

        if "commence avec" in reponse:
            joueurs = parties_uno[message.channel.id]["joueurs"]
            deck = creer_deck_uno()
            mains, deck = distribuer_mains(joueurs, deck)

            parties_uno[message.channel.id]["deck"] = deck
            parties_uno[message.channel.id]["mains"] = mains

            for joueur in joueurs:
                main = mains[joueur.id]
                cartes_txt = ", ".join([f"{c[0]} {c[1]}" for c in main])
                try:
                    await joueur.send(f"🃏 **Ta main de départ :**\n{cartes_txt}")
                except:
                    await message.channel.send(f"❌ Impossible d’envoyer la main à {joueur.display_name} (DMs fermés ?)")

            premiere_carte, deck = tirer_premiere_carte(deck)
            parties_uno[message.channel.id]["carte_visible"] = premiere_carte
            await message.channel.send(f"📤 **Carte visible de départ :** {premiere_carte[0]} {premiere_carte[1]}")

            joueur_actuel = joueurs[0]
            parties_uno[message.channel.id]["joueur_actuel"] = joueur_actuel.id
            await message.channel.send(f"🕐 C’est à **{joueur_actuel.display_name}** de jouer !\nTape `!play couleur valeur` ou `!uno draw`.")
        return

    if content == "uno start" and message.channel.id == 1363967793669738626:
        initialiser_partie_uno(message.channel.id)
        await message.channel.send("🃏 Une nouvelle partie de UNO est lancée ! Tape `!uno join` pour rejoindre (max 4 joueurs).")
        return

    if content == "uno join" and message.channel.id == 1363967793669738626:
        reponse = rejoindre_partie_uno(message.channel.id, message.author)
        await message.channel.send(reponse)
        return
    

    if content == "uno draw" and message.channel.id == 1363967793669738626:
        reponse = uno_piocher(message.channel.id, message.author.id)
        await message.channel.send(reponse)
        return

    if content == "uno main" and message.channel.id == 1363967793669738626:
        await uno_main(message)
        return

    if content.startswith("play") and message.channel.id == 1363967793669738626:
        try:
            parts = content.split(" ")
            if len(parts) == 4 and parts[1] == "noir":
                # Carte noire + choix de couleur
                couleur, valeur, couleur_choisie = parts[1], parts[2], parts[3]
                reponse = jouer_carte_avec_noir(message.channel.id, message.author.id, couleur, valeur, couleur_choisie)
            elif len(parts) == 3:
                # Carte classique
                couleur, valeur = parts[1], parts[2]
                reponse = jouer_carte_avancee(message.channel.id, message.author.id, couleur, valeur)
            else:
                reponse = "❌ Format incorrect. Tape : `!play rouge 3` ou `!play noir +4 jaune`"
        except Exception as e:
            reponse = f"❌ Erreur lors de la lecture de la commande : {str(e)}"

        await message.channel.send(reponse)
        return


    if content == "uno quit" and message.channel.id == 1363967793669738626:
        reponse = quitter_partie_uno(message.channel.id, message.author.id)
        await message.channel.send(reponse)
        return

    if content == "uno reset" and message.channel.id == 1363967793669738626:
        reponse = reset_partie_uno(message.channel.id)
        await message.channel.send(reponse)
        return


    # Commande !croquette
    if content == "croquette" and "croquette" in scores.get(str     (message.    author.id), {}):
        score_croquette = scores[str(message.author.id)]["croquette"]
        await update_role(message, "croquette", score_croquette)

    # Commande !connerie 

    if message.content.lower().startswith("!connerie"):
        connerie = get_connerie_vraie(message.guild)
        await message.channel.send(connerie)
        return
    if message.content.lower().startswith("!pardon"):
        reponse = commande_pardon()
        await message.channel.send(reponse)
        return

    if message.content.lower().startswith("!vengeance"):
        reponse = commande_vengeance()
        await message.channel.send(reponse)
        return
    if message.content.lower().startswith("!vengeance"):
        if peut_se_venger(message.author.id):
            reponse = commande_vengeance()
        else:
            reponse = "😼 Tu n'es pas la victime d’aujourd’hui. Patate t’ignore royalement."
        await message.channel.send(reponse)
        return


    # Commande !croquette
    if message.content.lower().startswith("!croquette"):
        user_id = str(message.author.id)
        reponse = commande_croquette(user_id)
        await message.channel.send(reponse)
        return

    # Commandes classiques : patate, croquette, ronron...
    if content in repliques_commandes:
        reponse = random.choice(repliques_commandes[content])
        await message.channel.send(reponse)
        return
    if message.content.lower().startswith("!etat"):
        reponse = commande_etat()
        await message.channel.send(reponse)
        return

    # Commande !tutos
    elif content == "tutos":
        tutos_txt = (
            "**📚 Tutos et trucs utiles recommandés par Patate :**\n\n"
            "🎨 **Dessin & création** :\n"
            "- [Comment dessiner un chat mignon (FR)](https://www.youtube.com/watch?v=2Y7KX6xLpx4)\n"
            "- [DrawingWiffWaffles (EN, fun et chill)](https://www.youtube.com/@DrawingWiffWaffles)\n"
            "- [Tuto perspective simple](https://www.youtube.com/watch?v=_i0fEHJpKj4)\n"
            "\n"
            "🛠️ **Apprendre des trucs cools** :\n"
            "- [Expériences marrantes à faire chez soi (FR)](https://www.youtube.com/watch?v=NUDFUKMhjiU)\n"
            "- [CrashCourse (EN, toutes les matières)](https://www.youtube.com/@crashcourse)\n"
            "\n"
            "🧠 Tu veux un tuto spécifique ? Demande à Patate, il connaît tout. Même comment plier une pizza en avion."
        )
        await message.channel.send(tutos_txt)

    elif content == "jeux":
        jeux_txt = (
            "**🎮 Jeux disponibles avec Patate uniquement dans le salon <#1363967793669738626> :**\n"
            "• `!devine` → Devine un chiffre entre 1 et 10 (Patate triche parfois)\n"
            "• `!pendu` → Le pendu... avec jugement à chaque erreur\n"
            "• `!bac` → Le Baccalauréat version Patate (12 catégories + mauvaise foi)\n"
             "• `!uno` → Le jeu de cartes où les amis ne comptent pas !\n"
            "\n"
            "📊 Pour voir ton score : `!stats`\n"
            "🏆 Pour voir les meilleurs : `!top devine` / `!top pendu` / `!top bac`\n"
            "🛑 Pour abandonner un jeu : `!stop`\n"
            "\n"
            "Patate peut être gentil... ou pas. Mais il t’observe. 👁️"
        )
        await message.channel.send(jeux_txt)

    # Commande spéciale : !humain
    if content.startswith("humain"):
        heure = datetime.datetime.now().hour
        if 6 <= heure < 12:
            moment = "matin"
        elif 12 <= heure < 18:
            moment = "après-midi"
        elif 18 <= heure < 23:
            moment = "soirée"
        else:
            moment = "nuit"

        user_id = str(message.author.id)
        contenu = repliques_humain.get(user_id, repliques_humain["default"])
        message_txt = random.choice(contenu[moment])
        await message.channel.send(message_txt)
    
    # Commande !pepette

    elif content == "pepette":
        await message.channel.send("Petite chose insignifiante ! MINUSCULE être bipède !")

    # Commande !meteo (absurde)

    elif content == "meteo":
        reponse = random.choice(repliques_commandes["meteo"])
        await message.channel.send(f"{reponse}")
    
    # commande !meteo reelle

    elif content.startswith("meteo"):
        ville = content[6:].strip()

        api_key = os.getenv("WEATHER_API_KEY")
        url = f"https://api.openweathermap.org/data/2.5/weather?q={ville}&appid={api_key}&lang=fr&units=metric"

        try:
            reponse = requests.get(url)
            data_meteo = reponse.json()

            if reponse.status_code == 200:
                nom = data_meteo['name']
                temp = data_meteo['main']['temp']
                desc = data_meteo['weather'][0]['description']

                await message.channel.send(f"Météo à {nom} : {temp}°C {desc}")
            else:
                await message.channel.send("Je ne connais pas cet endroit chelou, réessaye !")
        except Exception as e:
            await message.channel.send("Echec météo ! Le serveur est en PLS !")

    # commande info du jour

    elif content == "infodujour":
        try:
            url_news = f"https://newsapi.org/v2/everything?q=france&language=fr&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
            res = requests.get(url_news)
            data_news = res.json()

            if res.status_code == 200 and data_news["articles"]:
                article = random.choice(data_news["articles"])
                titre = article["title"]
                source = article["source"]["name"]

                await message.channel.send(f"({source}) : {titre}")
            else:
                await message.channel.send("Aucun cerveau n'a pondu de nouvelle aujourd'hui !")
        except Exception as e:
            await message.channel.send("J'ai tenté de m'informé... Erreur 404 NOT FOUND !")
    
    # reaction aux dessins dans nos beaux arts !

    if message.channel.id == 1207302926939463741 and message.attachments:
        if message.author != client.user:
            try:
                await message.add_reaction("<:chaLove:982623525317779456>")
                await message.add_reaction("<:chaFete:983750287632248842>")
                await message.add_reaction("<:chaGG:982349297288900678>")

                critique = random.choice(repliques_commandes["critiques_dessin"])
                await message.channel.send(f"{critique}")

            except discord.errors.HTTPException:
                await message.channel.send("J'ai tenté d'exprimer mes émotions mais Discord m'a snobé !")

    # commande jeux !pendu

    elif content == "pendu" and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)

        if user_id in pendu_en_cours:
            await message.channel.send("Tu as déjà une partie en cours, cervelle de croquette.")
            return

        mot = random.choice(mots_pendu).lower()
        lettres = []
        mot_affiche = " ".join(["__" for _ in mot])

        pendu_en_cours[user_id] = {
            "mot": mot,
            "affiche": mot_affiche,
            "lettres_trouvees": lettres,
            "tentatives": 0,
            "max": 7
        }

        await message.channel.send(f"Patate t’a choisi un mot. Bonne chance, larve.\n{mot_affiche}\nTentatives restantes : 7")
        await message.channel.send(
            "**📜 Commandes du jeu :**\n"
            "`!lettre x` → pour proposer une lettre\n"
            "`!tout motentier` → pour tenter le mot entier\n"
            "`!indice` → Patate révèle une lettre (coûte 1 tentative)\n"
            "`!mot` → pour voir l’état actuel\n"
            "`!stop` → abandonner\n"
            "`!stats pendu` / `!top pendu` → score et classement"
        )

    elif content.startswith("lettre ") and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)

        if user_id not in pendu_en_cours:
            await message.channel.send("T’as pas de partie en cours. Commence avec `!pendu`.")
            return

        try:
            lettre = content.split(" ")[1].lower()
            if len(lettre) != 1 or not lettre.isalpha():
                await message.channel.send("Une lettre. Pas un roman, bipède.")
                return
        except IndexError:
            await message.channel.send("Tape comme ça : `!lettre a`.")
            return

        partie = pendu_en_cours[user_id]
        mot = partie["mot"]
        lettres = partie["lettres_trouvees"]
        tentatives = partie["tentatives"]
        max_try = partie["max"]

        if lettre in lettres:
            await message.channel.send("T'as déjà proposé cette lettre, cerveau en boucle.")
            return

        lettres.append(lettre)
        nouvelle_affiche = " ".join([f"**{l.upper()}**" if l in lettres else "__" for l in mot])
        partie["affiche"] = nouvelle_affiche

        if lettre in mot:
            if "__" not in nouvelle_affiche:
                await message.channel.send(f"{nouvelle_affiche}\n🎉 Victoire ! Tu as trouvé le mot **{mot.upper()}**.\nPatate t’ignore majestueusement.")

                if user_id not in scores:
                    scores[user_id] = {}
                if "pendu" not in scores[user_id]:
                    scores[user_id]["pendu"] = {"victoires": 0, "defaites": 0}
                scores[user_id]["pendu"]["victoires"] += 1
                sauvegarder_scores()
                del pendu_en_cours[user_id]
            else:
                await message.channel.send(f"Bonne lettre...\n{nouvelle_affiche}\nTentatives restantes : {max_try - tentatives}")
        else:
            partie["tentatives"] += 1

            if partie["tentatives"] >= max_try:
                if user_id not in scores:
                    scores[user_id] = {}
                if "pendu" not in scores[user_id]:
                    scores[user_id]["pendu"] = {"victoires": 0, "defaites": 0}
                scores[user_id]["pendu"]["defaites"] += 1
                sauvegarder_scores()
                await message.channel.send(f"💀 Échec total. Le mot était **{mot.upper()}**.")
                del pendu_en_cours[user_id]
            else:
                await message.channel.send(f"Mauvaise lettre.\n{nouvelle_affiche}\nTentatives restantes : {max_try - partie['tentatives']}")

    elif content == "mot" and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)

        if user_id not in pendu_en_cours:
            return

        partie = pendu_en_cours[user_id]
        mot = partie["mot"]
        lettres = partie["lettres_trouvees"]
        affiche = " ".join([f"**{l.upper()}**" if l in lettres else "__" for l in mot])
        tentatives = partie["tentatives"]
        max_try = partie["max"]

        reponse = f"Mot actuel : {affiche}\n"
        reponse += f"Lettres tentées : `{', '.join(lettres) if lettres else 'Aucune'}`\n"
        reponse += f"Tentatives restantes : {max_try - tentatives}"

        await message.channel.send(reponse)

    elif content == "indice" and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)
        if user_id not in pendu_en_cours:
            await message.channel.send("Indice de quoi ? T’as même pas commencé.")
            return

        partie = pendu_en_cours[user_id]
        mot = partie["mot"]
        lettres = partie["lettres_trouvees"]
        possibles = [l for l in set(mot) if l not in lettres]

        if not possibles:
            await message.channel.send("Je t’ai déjà tout donné. C’est fini.")
            return

        nouvelle_lettre = random.choice(possibles)
        lettres.append(nouvelle_lettre)
        partie["tentatives"] += 1
        nouvelle_affiche = " ".join([f"**{l.upper()}**" if l in lettres else "__" for l in mot])
        partie["affiche"] = nouvelle_affiche

        await message.channel.send(f"Patate te révèle la lettre **{nouvelle_lettre.upper()}**.\n{nouvelle_affiche}\nTentatives restantes : {partie['max'] - partie['tentatives']}")

    elif content.startswith("tout ") and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)
        if user_id not in pendu_en_cours:
            await message.channel.send("T’essaies de tout deviner alors que t’as rien lancé ? Pathétique.")
            return

        mot_propose = content[5:].strip().lower()
        partie = pendu_en_cours[user_id]
        mot = partie["mot"]

        if mot_propose == mot:
            partie["affiche"] = " ".join([f"**{l.upper()}**" for l in mot])
            await message.channel.send(f"🎉 T’as trouvé le mot **{mot.upper()}** ! Respect (limité) de Patate.")
            if user_id not in scores:
                scores[user_id] = {}
            if "pendu" not in scores[user_id]:
                scores[user_id]["pendu"] = {"victoires": 0, "defaites": 0}
            scores[user_id]["pendu"]["victoires"] += 1
            sauvegarder_scores()
            del pendu_en_cours[user_id]
        else:
            partie["tentatives"] += 1
            if partie["tentatives"] >= partie["max"]:
                if user_id not in scores:
                    scores[user_id] = {}
                if "pendu" not in scores[user_id]:
                    scores[user_id]["pendu"] = {"victoires": 0, "defaites": 0}
                scores[user_id]["pendu"]["defaites"] += 1
                sauvegarder_scores()
                await message.channel.send(f"❌ Mauvais mot. Le bon mot était **{mot.upper()}**. Game over.")
                del pendu_en_cours[user_id]
            else:
                await message.channel.send(f"Faux mot. Tu viens de perdre une tentative.\n{partie['affiche']}\nTentatives restantes : {partie['max'] - partie['tentatives']}")

    elif content == "stop" and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)

        if user_id in pendu_en_cours:
            del pendu_en_cours[user_id]
            await message.channel.send("Tu fuis le pendu ? T’étais proche, ou pas. On saura jamais.")
        elif user_id in bac_en_cours:
            del bac_en_cours[user_id]
            await message.channel.send("Patate a gribouillé ta lettre. Elle n’existe plus.")
        else:
            await message.channel.send("Y’a rien à arrêter, bipède agité.") 

    # commande !devine (devine un chiffre entre 1 à 10)

    elif content.startswith("devine") and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)

        try:
            guess = int(content.split(" ")[1])
            if not 1 <= guess <= 10:
                await message.channel.send("C'est entre 1 et 10 on a dit, cerveau lent")
                return
        except (IndexError, ValueError):
            await message.channel.send("Tape genre : `!devine 4`")
            return

        if user_id not in scores:
            scores[user_id] = {"victoires": 0, "defaites": 0}

        if user_id not in parties_en_cours:
            chiffre = random.randint(1, 10)
            if random.randint(1, 3) == 1:
                chiffre += random.choice([-1, 1])
                chiffre = max(1, min(10, chiffre))
            await message.channel.send("Peut être bien que j'ai changé le chiffre... ou peut être pas !")
            parties_en_cours[user_id] = chiffre
            return

        # Partie en cours
        cible = parties_en_cours[user_id]

        if guess == cible:
            await message.channel.send("🎯 Patate > QUOI ?! Tu as trouvé ? Ok, t’as gagné. Pour cette fois.")
            scores[user_id]["victoires"] += 1
            del parties_en_cours[user_id]
        else:
            if guess < cible:
                await message.channel.send("📉 Patate > Trop petit... comme ton intelligence.")
            else:
                await message.channel.send("📈 Patate > Trop grand... comme ton égo.")
            scores[user_id]["defaites"] += 1

        sauvegarder_scores()

    elif content == "stats" and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)
        pseudo = message.author.display_name

        msg = f"📊 Stats de **{pseudo}** :\n"

        # Devine
        if "devine" in scores.get(user_id, {}):
            d = scores[user_id]["devine"]
            msg += f"🎯 Devine : {d.get('victoires', 0)} victoire(s), {d.get('defaites', 0)} défaite(s)\n"
        else:
            msg += "🎯 Devine : Tu n’as jamais deviné. T’as peur des chiffres ?\n"

        # Pendu
        if "pendu" in scores.get(user_id, {}):
            p = scores[user_id]["pendu"]
            msg += f"🔤 Pendu : {p.get('victoires', 0)} victoire(s), {p.get('defaites', 0)} défaite(s)\n"
        else:
            msg += "🔤 Pendu : Pas une seule corde testée...\n"

        # Baccalauréat
        if "baca" in scores.get(user_id, {}):
            b = scores[user_id]["baca"]
            msg += f"🧠 Baccalauréat : {b.get('points', 0)} point(s) en {b.get('parties', 0)} partie(s)\n"
        else:
            msg += "🧠 Baccalauréat : 0/20. T’as même pas sorti un fruit.\n"

        # Croquette
        if "croquette" in scores.get(user_id, {}):
            c = scores[user_id]["croquette"]
            msg += f"🍽️ Croquettes offertes : {c} (Patate s’en souvient… toujours.)\n"
        else:
            c = 0
            msg += "🍽️ Croquettes offertes : 0. Tu veux qu’il crève, c’est ça ?\n"

        msg += "\nPatate a jugé. Tu peux pleurer maintenant."

        # upload roles

        score_devine = d.get("victoires", 0) if "devine" in scores.get(user_id, {}) else 0
        score_pendu = p.get("victoires", 0) if "pendu" in scores.get(user_id, {}) else 0
        score_bac = b.get("points", 0) if "baca" in scores.get(user_id, {}) else 0
        score_croquette = scores.get(user_id, {}).get("croquette", 0)

        await update_role(message, "devine", score_devine)
        await update_role(message, "pendu", score_pendu)
        await update_role(message, "bac", score_bac)
        await update_role(message, "croquette", score_croquette)

        await message.channel.send(msg)

    # Mise à jour du rôle "croquette" partout, même hors #jouons
    if "croquette" in scores.get(str(message.author.id), {}):
        score_croquette = scores[str(message.author.id)]["croquette"]
        await update_role(message, "croquette", score_croquette)

    elif content == "top":
        if not scores:
            await message.channel.send("Personne ne s’est battu pour mon respect. Pathétique.")
            return

        classement = sorted(scores.items(), key=lambda x: x[1]["victoires"], reverse=True)
        top_3 = classement[:3]

        message_top = "**🏆 Top 3 des bipèdes qui osent jouer avec Patate :**\n"
        for i, (user_id, data) in enumerate(top_3, 1):
            try:
                membre = await message.guild.fetch_member(int(user_id))
                nom = membre.display_name if membre else "Inconnu"
            except:
                nom = "Inconnu"
            message_top += f"{i}. {nom} - {data['victoires']} victoire(s)\n"

        await message.channel.send(message_top)
    
    if content == "badge" or content == "badges":
        reponse = get_badges_utilisateur(message)
        await message.channel.send(reponse)
        return


    elif content == "miaou":
        msg = (
            "```\n"
            "        /\\_/\\  \n"
            "        ( o.o )  \n"
            "         > ^ <   \n"
            "```\n"
            "Salut, je suis **Votre-Chajesté mignon**, que veux-tu humain(e) ?\n\n"
            "** Voici mes commandes disponibles :**\n"
            "Ces commandes sont dispo UNIQUEMENT dans le salon <#1363967793669738626>\n\n"
            "🟢 `!jeux` → Affiche la liste des jeux\n"
            "📊 `!stats` → Tes scores globaux\n"
            "🏆 `!top [jeu]` → Classement d’un jeu (`devine`, `pendu`, `bac`)\n"
            "🛑 `!stop` → Quitter une partie\n"
            "🎓 `!bac` → Le baccalauréat vache\n"
            "🔤 `!pendu` → Le pendu qui juge\n"
            "🎯 `!devine` → Devine un chiffre (spoiler : Patate triche)\n"
            "`Commandes pour le Jeu UNO !\n"
            "`🎴 Commandes du jeu UNO (uniquement dans #jouons) :\n\n"
            "`!uno start` → Crée une nouvelle partie UNO\n"
            "`!uno join` → Rejoins la partie (2 à 4 joueurs)\n"
            "`!uno quit` → Quitte la partie (Patate ne t’en voudra que quelques années)• \n"
            "`!uno reset` → Réinitialise entièrement la partie en cours\n"
            "🏆 Le premier à ne plus avoir de carte remporte la partie. Patate jugera... avec classe.\n\n"
            "Ces commandes sont dispo partout sur le serveur\n\n"
            "📚 `!tutos` → Une sélection de tutos pour t’améliorer\n"
            "😺 `!miaou` → C’est ici, idiot.\n"
            "🐉 `!pepette`→ Spécial <#1357021254758043853> ! \n"
            "✨ `!meteo`→ Peut être que je vais te répondre... \n"
            "☀️ `!meteo [Ville]`→ La vraie météo ! \n"
            "🌍 `!infodujour`→ Te donne une actualité du jour (importante... ou pas). \n"
            "🐈‍⬛ `!patate`→ Je vais te juger fort ! \n"
            "😼 `!humain`→ Douce phrase, rien que pour toi, selon l'heure ! \n"
            "🫘 `!croquette`→ Donne moi à manger ! \n"
            "😻 `!ronron`→ Un peu d'amour 😽! \n"
            "🤪 `!connerie`→ Le cluedo félin ! \n"
            "😈 `!vengeance`→ Tu peux essayer de te venger si tu veux ! \n"
            "<:chaTimide:984218971060445205> `!pardon`→ Demande pardon à Sa Chajesté et peut être il te sera accordé ! \n"
            "🏆 `!badges`→ Tu peux voir tous tes badges obtenus ! \n"
            "`\n\n"

        )
        await message.channel.send(msg)
    
    # Commande !bac

    elif content == "bac" and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)

        lettre = random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        bac_en_cours[user_id] = lettre

        await message.channel.send(f"Lettre choisie : **{lettre}**.\nUtilise la commande : `!baca mot1 mot2 mot3 ... mot12`")
        await message.channel.send(
            "**📚 Catégories :**\n"
            "1. Animal\n2. Objet\n3. Prénom\n4. Insulte\n5. Lieu\n6. Métier\n"
            "7. Mot en anglais\n8. Couleur\n9. Partie du corps\n10. Fruit/Légume\n11. Marque\n12. Film/Série/Animé\n\n"
            "**Commandes :**\n"
            "`!baca` suivi de tes 12 mots (ex : !baca araignée arrosoir alice abruti angers avocat apple abricot audi rouge bras pocahontas)`\n"
            "`!stats baca` → ton score\n`"
            "`!top baca` → classement suprême"
        )

    elif content.startswith("baca ") and message.channel.id == 1363967793669738626:
        user_id = str(message.author.id)
        if user_id not in bac_en_cours:
            await message.channel.send("Tu dois d'abord lancer une partie avec `!bac`. Oui, même toi.")
            return

        lettre = bac_en_cours[user_id].upper()
        reponses = content.split(" ")[1:]

        if len(reponses) != 12:
            await message.channel.send(f"Tu m’as donné {len(reponses)} mot(s)... Il m’en faut 12.\nExemple : `!baca mot1 mot2 ... mot12`.")
            return

        categories = [
            "Animal", "Objet", "Prénom", "Insulte", "Lieu", "Métier",
            "Mot en anglais", "Couleur", "Partie du corps", "Fruit/Légume",
            "Marque", "Film/Série/Animé"
        ]

        points = 0
        feedback = []

        for i, mot in enumerate(reponses):
            mot_clean = mot.strip()
            if not mot_clean.lower().startswith(lettre.lower()):
                feedback.append(f"❌ {categories[i]} : {mot_clean} (doit commencer par {lettre})")
                continue

            if not mot_clean.isalpha() or len(mot_clean) < 2 or len(mot_clean) > 25:
                feedback.append(f"❌ {categories[i]} : {mot_clean} (mot suspect... Patate doute de ton sérieux)")
                continue

            feedback.append(f"✅ {categories[i]} : {mot_clean}")
            points += 1

        if user_id not in scores:
            scores[user_id] = {}
        if "baca" not in scores[user_id]:
            scores[user_id]["baca"] = {"points": 0, "parties": 0}

        scores[user_id]["baca"]["points"] += points
        scores[user_id]["baca"]["parties"] += 1
        sauvegarder_scores()

        del bac_en_cours[user_id]

        await message.channel.send("\n".join(feedback) + f"\n**Total : {points}/12 points.**" + ("f\n<:chaFete:983750287632248842> Félicitations, t’as tout bon !" if points == 12 else ""))

client.run(TOKEN)