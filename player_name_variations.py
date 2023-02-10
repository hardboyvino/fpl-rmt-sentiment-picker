"""
Because users use all forms of spellings for each player, this file used as a repository of the different player name spellings.

This file is updated on a weekly basis to keep up with the new weird spellings.
"""


def player_name_vars():
    """create a dict with all possible variations of all player names"""
    player_var_names = {
        "Haaland": ["haaland", "hÃ¥land", "hauland", "halaand", "harlaand", "haaaland", "haalands"],
        "Trippier": ["trippier", "tripper", "trips", "tripps", "tripp", "trip"],
        "Kane": ["kane"],
        "Ødegaard": ["odegaard", "Ã¸degaard", "odeegard", "odegard", "Ã¸gegÃ¥rd", "odeg", "degaard", "ode", "odergaard"],
        "Almirón": ["almiron", "almoron", "almirion", "almirÃ³n", "almerion", "almiroon"],
        "Toney": ["toney"],
        "Saka": ["saka"],
        "Rashford": ["rashford", "rash", "rashy"],
        "De Bruyne": ["kdb", "bruyne", "kevin", "kev"],
        "Pope": ["pope"],
        "Salah": ["salah"],
        "Martinelli": ["martinelli", "martineli", "nelli"],
        "Schär": ["schÃ¤r", "schar"],
        "Rodrigo": ["rodrigo"],
        "Raya": ["raya"],
        "Saliba": ["saliba", "sailiba"],
        "Groß": ["groÃŸ", "gros", "gross", "grob"],
        "March": ["march"],
        "Burn": ["burn"],
        "Fernandes": ["bruno", "fernandes", "fernandez", "fernandez", "penandes"],
        "Gabriel": ["gabriel"],
        "Botman": ["botman", "bottman"],
        "Trossard": ["trossard"],
        "White": ["white"],
        "Alisson": ["allison"],
        "Mitrović": ["mitro", "mitrovic", "mitroviÄ‡"],
        "Henderson": ["henderson"],
        "Sá": ["sa"],
        "Ramsdale": ["ramsdale"],
        "Foden": ["foden"],
        "Højbjerg": ["hojbjerg"],
        "Mee": ["mee"],
        "Xhaka": ["xhaka"],
        "Andreas": ["andreas"],
        "Maddison": ["maddison"],
        "Zaha": [],
        "De Gea": ["gea", "ddg", "degea"],
        "Ederson": ["ederson"],
        "Barnes": ["barnes"],
        "Bowen": ["bowen"],
        "Eze": ["eze"],
        "Mount": ["mount"],
        "Ward-Prowse": [],
        "Eriksen": ["eriksen"],
        "Guaita": ["guaita"],
        "Leno": [],
        "Son": [],
        "Cancelo": ["cancelo"],
        "Fabianski": [],
        "Gibbs-White": [],
        "Lloris": ["lloris"],
        "Willock": [],
        "Adams": [],
        "Bailey": ["bailey"],
        "Bernardo": [],
        "Castagne": ["castagne"],
        "Iwobi": [],
        "Firmino": ["firmino"],
        "Jensen": [],
        "Jesus": [],
        "Sánchez": [],
        "Ward": ["ward"],
        "Podence": [],
        "Watkins": ["watkins"],
        "Mac Allister": ["macallster", "allister"],
        "Mahrez": ["mahrez"],
        "Bruno Guimarães": ["guimaraes"],
        "Neves": ["neves"],
        "Shaw": ["shaw"],
        "Billing": [],
        "De Cordova-Reid": [],
        "Perišić": ["perisic", "persic"],
        "Dier": ["dier"],
        "Gray": [],
        "Olise": [],
        "Tielemans": [],
        "Arrizabalaga": ["kepa", "arrizabalaga", "keppa"],
        "Bentancur": [],
        "Dewsbury-Hall": ["kdh"],
        "Havertz": ["havertz"],
        "Johnson": [],
        "Martínez": ["martinez", "lisandro", "martÃ­nez"],
        "Mbeumo": ["mbuemo", "mbeumo"],
        "Meslier": ["meslier"],
        "Thiago Silva": ["thiago"],
        "Bernando Silva": ["silva"],
        "Wilson": ["wilson"],
        "Douglas Luiz": [],
        "Pickford": ["pickford"],
        "Solanke": ["solanke"],
        "Ream": [],
        "Robertson": ["robertson", "robbo"],
        "Sterling": [],
        "Tavernier": [],
        "Rodri": [],
        "Struijk": ["struijk"],
        "Davies": [],
        "Gündogan": [],
        "Joelinton": [],
        "Buendía": ["buendia"],
        "Ings": [],
        "Palhinha": [],
        "Reed": [],
        "Van Dijk": ["vvd"],
        "Wissa": [],
        "Zouma": [],
        "Casemiro": ["casemiro", "cassemiro"],
        "Coady": [],
        "Harrison": [],
        "Kulusevski": ["kulusevski", "kulu"],
        "Alexander-Arnold": ["taa", "trent"],
        "Mitoma": ["mitoma", "mitomaâ€¦", "motoma", "mitimo"],
        "S.Longstaff": [],
        "Willian": [],
        "Henry": [],
        "Mings": ["mings"],
        "Rice": [],
        "Aaronson": [],
        "Kilman": ["kilman"],
        "Stones": ["stones"],
        "Darwin": ["darwin", "nunez", "darwins"],
        "Grealish": ["grealish"],
        "Janelt": [],
        "Partey": [],
        "Ramsey": [],
        "Dunk": ["dunk"],
        "Veltman": [],
        "Young": [],
        "Aurier": ["aurier"],
        "Dasilva": [],
        "Lerma": [],
        "Moore": [],
        "Awoniyi": [],
        "Bazunu": [],
        "Dalot": ["dalot"],
        "Konsa": [],
        "Soucek": [],
        "Zinchenko": ["zinchenko"],
        "Jorginho": ["jorginho"],
        "Vardy": [],
        "Ayew": [],
        "Benrahma": ["said", "benrama", "benrahma"],
        "Cucurella": ["cucurella", "cucu"],
        "Gomez": ["gomez"],
        "Koulibaly": [],
        "Varane": ["varane"],
        "Lallana": [],
        "Mykolenko": [],
        "Onana": [],
        "Amartey": ["amartey"],
        "Andersen": ["andersen"],
        "Edouard": [],
        "Tarkowski": ["takowski", "tarkowski"],
        "Daka": [],
        "Emerson Royal": [],
        "Justin": [],
        "Perraud": ["perraud"],
        "Summerville": [],
        "Caicedo": [],
        "Mitchell": [],
        "Welbeck": [],
        "Akanji": ["akanji"],
        "Antonio": [],
        "Cook": [],
        "Estupiñán": ["estupian", "estu", "estupinan", "estupiÃ±an", "eustupinan", "estupunian"],
        "Gordon": [],
        "Guéhi": ["guehi"],
        "Robinson": [],
        "Collins": [],
        "Cresswell": [],
        "Nketiah": ["nketiah", "nkehtia", "eddie", "nkeitah", "nkeitha", "nkethia", "nkethiah", "nketia"],
        "Schlupp": [],
        "Smith": [],
        "Tete": [],
        "Aké": [],
        "Aribo": [],
        "Dias": ["dias"],
        "Elliott": [],
        "Scamacca": [],
        "Álvarez": ["alvarez"],
        "Faes": ["faes"],
        "McNeil": [],
        "Moutinho": [],
        "Roca": [],
        "Sancho": ["sancho"],
        "A.Armstrong": [],
        "Antony": ["antony"],
        "Diop": [],
        "Luis Díaz": [],
        "Matheus": [],
        "Nørgaard": [],
        "Paquetá": [],
        "Anthony": [],
        "Pinnock": [],
        "Saint-Maximin": [],
        "Yates": [],
        "Azpilicueta": ["azpilicueta", "azpi"],
        "C.Doucouré": [],
        "Fornals": [],
        "Digne": ["digne"],
        "Malacia": ["malacia"],
        "McGinn": [],
        "Wood": [],
        "Chalobah": [],
        "Christie": [],
        "Doherty": ["doherty"],
        "Elyounoussi": [],
        "Kebano": [],
        "Kehrer": [],
        "Murphy": [],
        "N.Williams": ["williams", "nico", "neco"],
        "Zemura": [],
        "Koch": [],
        "R.Sessegnon": [],
        "Webster": [],
        "Worrall": [],
        "Aït-Nouri": [],
        "Fred": [],
        "Roerslev": [],
        "Adama": [],
        "Chilwell": [],
        "Fabinho": [],
        "Freuler": [],
        "Gueye": [],
        "Jonny": [],
        "Martial": ["martial"],
        "Walker-Peters": [],
        "Gallagher": ["gallagher"],
        "McKenna": [],
        "Romero": [],
        "Salisu": [],
        "Coufal": [],
        "Lingard": [],
        "Semedo": [],
        "Tosin": [],
        "Guedes": [],
        "Pulisic": [],
        "Cooper": [],
        "Ferguson": ["ferguson"],
        "Kamara": [],
        "Neto": [],
        "Ajer": [],
        "Coleman": [],
        "Isak": ["isak"],
        "James": ["james"],
        "Kelly": [],
        "Kouyaté": [],
        "Kristensen": [],
        "S.Armstrong": [],
        "Tomiyasu": ["tomiyasu"],
        "Wan-Bissaka": ["wanbissaka", "awb"],
        "Boly": [],
        "Bueno": ["bueno", "beuno"],
        "Mepham": [],
        "Renan Lodi": [],
        "Walker": ["walker"],
        "Carvalho": [],
        "Kovacic": [],
        "Lenglet": [],
        "Loftus-Cheek": [],
        "Maupay": [],
        "Senesi": [],
        "Soumaré": [],
        "Travers": [],
        "Ayling": ["ayling"],
        "Bamford": ["bamford"],
        "Cairney": [],
        "Fábio Vieira": [],
        "Patterson": ["patterson", "padderson", "paterson"],
        "Richarlison": [],
        "Thiago": [],
        "Calvert-Lewin": [],
        "Clyne": [],
        "Hwang": [],
        "Mendy": [],
        "Sinisterra": [],
        "Targett": [],
        "Tsimikas": [],
        "Vinícius": [],
        "Bissouma": [],
        "Cash": [],
        "Coutinho": [],
        "Dendoncker": [],
        "Greenwood": ["greenwood"],
        "Iheanacho": ["iheanacho", "nacho"],
        "Lavia": [],
        "Milner": ["milner"],
        "O'Brien": [],
        "Tierney": [],
        "Zanka": [],
        "Aubameyang": [],
        "Broja": [],
        "Gnonto": ["gnonto", "gnoto", "gnotto"],
        "Dennis": [],
        "Djenepo": [],
        "Elanga": [],
        "Gelhardt": [],
        "Nelson": [],
        "Ronaldo": [],
        "Surridge": [],
        "Bella-Kotchap": [],
        "Caleta-Car": [],
        "Garnacho": [],
        "Mangala": [],
        "Mateta": [],
        "Ndidi": [],
        "Pérez": [],
        "Toffolo": [],
        "Ziyech": [],
        "Baptiste": [],
        "Chamberlain": [],
        "Edozie": [],
        "Mara": [],
        "McTominay": [],
        "Onyeka": [],
        "Jansson": ["jansson"],
        "Laporte": ["laporte"],
        "Dawson": [],
        "Llorente": [],
        "Praet": [],
        "Thomas": ["thomas"],
        "Colwill": [],
        "Diallo": [],
        "Maguire": ["maguire"],
        "Badiashile": [],
        "Lamptey": ["lamptey"],
        "Maitland-Niles": [],
        "Milivojevic": [],
        "Albrighton": [],
        "Emerson": [],
        "Hickey": [],
        "Lewis": ["lewis", "rico"],
        "Lewis-Potter": [],
        "Lyanco": [],
        "Mina": [],
        "Downes": [],
        "Holgate": [],
        "Hughes": [],
        "Klich": [],
        "Lindelöf": [],
        "Ogbonna": [],
        "Traoré": [],
        "Chukwuemeka": [],
        "Evans": [],
        "Fraser": [],
        "Mwepu": [],
        "Stephens": [],
        "Toti": [],
        "A.Doucouré": [],
        "Bajcetic": [],
        "Damsgaard": [],
        "Diego Costa": [],
        "Richards": [],
        "Sarmiento": [],
        "Aguerd": [],
        "Begović": [],
        "Bryan": [],
        "Fredericks": [],
        "Ghoddos": [],
        "Konaté": [],
        "Ake": ["ake"],
        "Matip": ["matip"],
        "Olsen": [],
        "Pearson": [],
        "Skipp": [],
        "Zakaria": [],
        "Anderson": [],
        "Colback": [],
        "Diogo Jota": ["jota"],
        "Hall": [],
        "Jiménez": [],
        "Lucas Moura": [],
        "Palmer": [],
        "Rothwell": [],
        "Sambi": [],
        "Undav": [],
        "Van de Beek": [],
        "Wöber": [],
        "Keita": [],
        "Mbabu": [],
        "Niakhaté": [],
        "Rodák": [],
        "Rondón": [],
        "Sergio Gómez": [],
        "Stansfield": [],
        "Álex Moreno": ["moreno"],
        "Archer": [],
        "Dembélé": [],
        "Elneny": [],
        "Enciso": [],
        "Forshaw": [],
        "Gilmour": [],
        "Holding": ["holding"],
        "Jones": [],
        "Campbell": [],
        "Canós": [],
        "Cornet": [],
        "Gakpo": ["gakpo"],
        "Garner": [],
        "Godfrey": [],
        "Kanté": [],
        "Lanzini": [],
        "Ouattara": [],
        "Smith Rowe": [],
        "Stacey": [],
        "Bech": [],
        "Bednarek": [],
        "Chambers": [],
        "Cunha": [],
        "Dervişoğlu": [],
        "Duffy": [],
        "Hennessey": [],
        "Hodge": [],
        "Larios": [],
        "Riedewald": [],
        "Spence": [],
        "Stanislas": [],
        "W.Fofana": [],
        "Weghorst": ["weghorst", "wegz"],
        "Diego Carlos": [],
        "Ebiowei": [],
        "Firpo": [],
        "Harris": [],
        "Phillips": [],
        "Sarr": [],
        "Shelvey": [],
        "Solomon": [],
        "Walcott": [],
        "Areola": [],
        "Augustinsson": [],
        "Biancone": [],
        "Cannon": [],
        "Cédric": [],
        "Dele": [],
        "Doak": [],
        "Forster": ["forster"],
        "Lemina": [],
        "Lowe": [],
        "Onomah": [],
        "Ritchie": [],
        "Romeu": [],
        "Sanson": [],
        "Scarpa": [],
        "Simms": [],
        "Söyüncü": [],
        "Van Hecke": [],
        "Vinagre": [],
        "Alcaraz": [],
        "Bevan": [],
        "Brunt": [],
        "Cafú": [],
        "Clark": [],
        "Coventry": [],
        "Danilo": [],
        "Drameh": [],
        "Francois": [],
        "Gyabi": [],
        "Hutchinson": [],
        "Kalajdžić": [],
        "Keane": [],
        "Krafth": [],
        "Kurzawa": [],
        "Lascelles": [],
        "Lembikisa": [],
        "Manquillo": [],
        "Marcondes": [],
        "Marquinhos": [],
        "Mateo Joseph": [],
        "Mighten": [],
        "Moran": [],
        "Mubama": [],
        "Mudryk": ["mudryk"],
        "Nwaneri": [],
        "Orsic": [],
        "Ozoh": [],
        "Redmond": [],
        "Ronan": [],
        "Sarabia": ["sarabia"],
        "Schade": [],
        "Tanganga": [],
        "Ablade": [],
        "Adrián": [],
        "Adu-Adjei": [],
        "Ahamada": [],
        "Allan": [],
        "Alonso": [],
        "Alzate": [],
        "Amad": [],
        "Ampadu": [],
        "Andrey Santos": [],
        "Sanchez": ["sanchez"],
        "André Gomes": [],
        "Arter": [],
        "Arthur": [],
        "Ashby": [],
        "Austin": [],
        "Ayari": [],
        "B.Williams": [],
        "Badé": [],
        "Bailly": [],
        "Balcombe": [],
        "Balmer": [],
        "Barkley": [],
        "Bate": [],
        "Bennett": [],
        "Benteke": [],
        "Bentley": [],
        "Bergwijn": [],
        "Bertrand": [],
        "Bettinelli": [],
        "Bidstrup": [],
        "Bishop": [],
        "Bogarde": [],
        "Branthwaite": [],
        "Braybrooke": [],
        "Bree": [],
        "Brooks": [],
        "Buonanotte": [],
        "Butland": [],
        "Butler-Oyedeji": [],
        "Caballero": [],
        "Carson": [],
        "Cavaleiro": [],
        "Chiquinho": [],
        "Choudhury": [],
        "Clarke": [],
        "Cox": [],
        "Cozier-Duberry": [],
        "Crama": [],
        "Cundle": [],
        "D.D.Fofana": [],
        "Dacosta Gonzalez": [],
        "Dale Taylor": [],
        "Dallas": [],
        "Danjuma": [],
        "Darlow": [],
        "Davis": [],
        "Delap": [],
        "Devine": [],
        "Dräger": [],
        "Dubravka": [],
        "Dummett": [],
        "Durán": [],
        "El Ghazi": [],
        "Enzo": [],
        "Fabio Silva": [],
        "Felipe": [],
        "Fernández": [],
        "Finnigan": [],
        "Forss": [],
        "Furlong": [],
        "Gayle": [],
        "Gazzaniga": [],
        "Gbamin": [],
        "Godo": [],
        "Gomes": [],
        "Goode": [],
        "Goodman": [],
        "Griffiths": [],
        "Guilbert": [],
        "H.Davies": [],
        "H.Traorè": [],
        "Hammond": [],
        "Hause": [],
        "Heaton": [],
        "Hein": [],
        "Hendrick": [],
        "Hill": [],
        "Hinshelwood": [],
        "Hjelde": [],
        "Hudson-Odoi": [],
        "Humphreys": [],
        "Iqbal": [],
        "Iroegbunam": [],
        "Iversen": ["iverson"],
        "Jakupović": [],
        "John": [],
        "Johnstone": [],
        "João Gomes": [],
        "Kadan Young": [],
        "Kamaldeen": [],
        "Karius": [],
        "Kelleher": [],
        "Kenedy": [],
        "Kesler Hayden": [],
        "Kiwior": [],
        "Klaesson": [],
        "Knight": [],
        "Knockaert": [],
        "Kongolo": [],
        "Kovár": [],
        "Kozłowski": [],
        "Kristiansen": [],
        "Kuol": [],
        "Laryea": [],
        "Lis": [],
        "Livramento": [],
        "Lolley": [],
        "Lukic": [],
        "Lyle Taylor": [],
        "Madueke": [],
        "Mainoo": [],
        "Marschall": [],
        "Masuaku": [],
        "Matthews": [],
        "Mbe Soh": [],
        "Mbete": [],
        "McArthur": [],
        "McAtee": [],
        "McAteer": [],
        "McCarthy": [],
        "McKennie": [],
        "Mills": [],
        "Moder": [],
        "Morgan": [],
        "Mosquera": [],
        "Muniz": [],
        "Nakamba": [],
        "Navas": [],
        "Nkounkou": [],
        "Ojeda": [],
        "Oko-Flex": [],
        "Onuachu": [],
        "Ortega": [],
        "Pablo Marí": [],
        "Panzo": [],
        "Parkes": [],
        "Parrott": [],
        "Payne": [],
        "Pedro Porro": [],
        "Pellistri": [],
        "Perkins": [],
        "Perrone": [],
        "Philogene-Bidace": [],
        "Plain": [],
        "Plange": [],
        "Pollock": [],
        "Price": [],
        "Pépé": [],
        "R.Williams": [],
        "Rak-Sakyi": [],
        "Ramsay": [],
        "Randolph": [],
        "Raphinha": [],
        "Reguilón": [],
        "Ricardo": [],
        "Roberts": [],
        "Robles": [],
        "Rodney": [],
        "Rodon": [],
        "Rutter": [],
        "Sabitzer": [],
        "Sadi": [],
        "Samba": [],
        "Saydee": [],
        "Scarlett": [],
        "Scherpen": [],
        "Schmeichel": [],
        "Sekularac": [],
        "Semenyo": [],
        "Shackleton": [],
        "Shoretire": [],
        "Sinisalo": [],
        "Smallbone": [],
        "Smithies": [],
        "Sousa": [],
        "Souttar": [],
        "Steele": [],
        "Steffen": [],
        "Stevens": [],
        "Strakosha": [],
        "Tavares": [],
        "Tella": [],
        "Telles": [],
        "Tetê": [],
        "Thompson": [],
        "Torreira": [],
        "Townsend": [],
        "Trevitt": [],
        "Turner": [],
        "Turns": [],
        "Vale": [],
        "Valery": [],
        "Van den Berg": [],
        "Vestergaard": ["vestegaard"],
        "Viña": [],
        "Vlasic": [],
        "Warrington": [],
        "Welch": [],
        "Wells-Morrison": [],
        "Werner": [],
        "Whitworth": [],
        "Wilson-Esbrand": [],
        "Winks": [],
        "Wormleighton": [],
        "Xande Silva": [],
        "Yarmolyuk": [],
        "Zabarnyi": [],
        "Šarkić": [],
        "Tomkins": [],
        "João Félix": ["felix"],
    }

    return player_var_names