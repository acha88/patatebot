import discord
import random
import datetime
import json
import os
import requests
from dotenv import load_dotenv

# -------- CONFIGURATION --------
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

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

# -------------- DISCORD ----------------------

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
intents.members = True  # Nécessaire pour détecter les arrivées et départs
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
        f"Bienvenue {member.mention} ! Patate t'observe... 👁️",
        f"Yo {member.name}, entre donc dans la folie de ce serveur.",
        f"{member.mention} vient d’arriver. Patate dit : 't’as intérêt à lire les règles'.",
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

    # Commandes classiques : patate, croquette, ronron...
    if content in repliques_commandes:
        reponse = random.choice(repliques_commandes[content])
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

        msg += "\nPatate a jugé. Tu peux pleurer maintenant."

        await message.channel.send(msg)

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
            "Ces commandes sont dispo partout sur le serveur"
            "📚 `!tutos` → Une sélection de tutos pour t’améliorer\n"
            "😺 `!miaou` → C’est ici, idiot.\n"
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