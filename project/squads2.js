/* ============================================================================
   squads2.js — projected squads for the remaining 24 contenders (the nations
   added when the field grew to 48). Merges into window.WC_SQUADS so lineups.js
   builds them exactly like the others. First 11 = projected XI.
   Format: [shirtNo, "Name", "POS", "Club", tier?]. Illustrative (≈2025/26).
   ========================================================================== */
(function () {
  window.WC_SQUADS = window.WC_SQUADS || {};
  Object.assign(window.WC_SQUADS, {

  QAT: ["4-3-3", [
    [1,"M. Barsham","GK","Al-Sadd"],[2,"Pedro Miguel","RB","Al-Sadd"],[15,"B. Khoukhi","CB","Al-Arabi"],[4,"T. Salman","CB","Al-Sadd"],[3,"A. Hassan","LB","Al-Sadd"],[12,"K. Boudiaf","CDM","Al-Duhail"],[23,"A. Madibo","CM","Al-Duhail"],[10,"H. Al-Haydos","CAM","Al-Sadd"],[11,"A. Afif","RW","Al-Sadd",1.3],[19,"A. Ali","ST","Al-Duhail",1.2],[17,"I. Mohammad","LW","Al-Duhail"],
    [22,"Y. Hassan","GK","Al-Gharafa"],[21,"S. Al-Sheeb","GK","Al-Sadd"],[5,"B. Al-Rawi","CB","Al-Gharafa"],[14,"H. Ahmed","LB","Al-Sadd"],[20,"S. Al-Brake","RB","Al-Sadd"],[6,"A. Hatim","CM","Al-Sadd"],[16,"M. Waad","CB","Al-Rayyan"],[8,"M. Muntari","ST","Al-Gharafa",1.1],[18,"Kh. Ali","RW","Al-Wakrah"],[24,"Y. Abdurisag","LW","Al-Sadd"],[25,"A. Alaaeldin","RW","Al-Gharafa"],[26,"T. Mohammed","CB","Al-Duhail"],
  ]],
  KSA: ["4-3-3", [
    [21,"M. Al-Owais","GK","Al-Hilal"],[2,"S. Al-Ghannam","RB","Al-Nassr"],[3,"A. Al-Bulaihi","CB","Al-Hilal"],[5,"H. Tambakti","CB","Al-Hilal"],[13,"Y. Al-Shahrani","LB","Al-Hilal"],[14,"A. Otayf","CDM","Al-Hilal"],[7,"M. Kanno","CM","Al-Hilal"],[8,"A. Al-Malki","CM","Al-Ahli"],[10,"S. Al-Dawsari","LW","Al-Hilal",1.3],[9,"F. Al-Buraikan","ST","Al-Ahli",1.2],[11,"S. Al-Shehri","RW","Al-Ittihad",1.1],
    [1,"N. Al-Aqidi","GK","Al-Nassr"],[22,"A. Al-Kassar","GK","Al-Riyadh"],[4,"A. Madu","CB","Al-Nassr"],[6,"S. Abdulhamid","RB","Roma"],[15,"A. Al-Amri","CB","Al-Hilal"],[16,"N. Al-Dawsari","CM","Al-Nassr"],[17,"S. Al-Najei","CM","Al-Nassr"],[23,"M. Al-Breik","RB","Al-Hilal"],[18,"A. Al-Hamdan","ST","Al-Shabab",1.1],[19,"H. Al-Tambakti","CB","Al-Hilal"],[20,"F. Al-Ghamdi","RW","Al-Ahli"],[12,"A. Al-Aboud","LM","Al-Nassr"],
  ]],
  UZB: ["4-3-3", [
    [1,"U. Yusupov","GK","Pakhtakor"],[4,"A. Khusanov","CB","Manchester City",1.1],[3,"R. Ashurmatov","CB","Gangwon"],[2,"F. Sayfiev","RB","Pakhtakor"],[5,"S. Nasrullaev","LB","Nasaf"],[6,"O. Shukurov","CDM","Arsenal Tula"],[8,"J. Masharipov","CAM","Pakhtakor",1.2],[7,"A. Fayzullaev","RW","CSKA Moscow",1.2],[10,"O. Urunov","LW","Neftchi"],[9,"E. Shomurodov","ST","Roma",1.3],[11,"A. Turgunboev","RW","Pakhtakor"],
    [12,"A. Nematov","GK","Pakhtakor"],[22,"V. Frolov","GK","Navbahor"],[13,"A. Khamdamov","CAM","Al-Shorta",1.1],[14,"I. Sergeev","ST","Pari NN",1.1],[15,"K. Tukhtakhujaev","CB","Pakhtakor"],[16,"J. Iskanderov","CM","Persepolis"],[17,"D. Ergashev","RM","Pakhtakor"],[18,"O. Zoteev","CB","Nasaf"],[19,"S. Khamrobekov","CM","Sochi"],[20,"A. Yusupov","LB","Bunyodkor"],[21,"S. Mullajanov","RB","Pakhtakor"],
  ]],
  IRN: ["4-3-3", [
    [1,"A. Beiranvand","GK","Tractor"],[2,"S. Moharrami","RB","Dinamo Zagreb"],[8,"M. Hosseini","CB","Kayserispor"],[19,"S. Khalilzadeh","CB","Tractor"],[3,"E. Hajsafi","LB","Aluminium"],[6,"S. Ezatolahi","CDM","Shabab Al-Ahli"],[4,"A. Nourollahi","CM","Shabab Al-Ahli"],[7,"A. Jahanbakhsh","RW","Heerenveen",1.2],[9,"M. Taremi","ST","Inter",1.4],[10,"S. Azmoun","LW","Shabab Al-Ahli",1.3],[20,"S. Ghoddos","CAM","Brentford"],
    [12,"P. Niazmand","GK","Sepahan"],[22,"H. Hosseini","GK","Esteghlal"],[5,"M. Mohammadi","LB","AEK Athens"],[13,"A. Aghasi","CB","Esteghlal"],[15,"M. Pouraliganji","CB","Persepolis"],[14,"S. Sadeghi","CDM","Persepolis"],[16,"M. Torabi","RW","Al-Shorta",1.1],[17,"A. Gholizadeh","LW","Lech Poznan",1.1],[11,"K. Ansarifard","ST","Omonia",1.1],[18,"A. Karimi","CM","Bayer Leverkusen"],[23,"A. Hosseinzadeh","LW","Esteghlal"],
  ]],
  JOR: ["4-3-3", [
    [21,"Y. Abulaila","GK","Al-Wehdat"],[4,"Y. Al-Arab","CB","Al-Faisaly"],[5,"A. Nasib","CB","Al-Hussein"],[2,"M. Abu Hashish","RB","Al-Faisaly"],[3,"S. Al-Ajalin","LB","Al-Wehdat"],[6,"N. Al-Rashdan","CDM","Al-Ahli"],[8,"N. Al-Rawabdeh","CM","APOEL"],[15,"M. Al-Mardi","CM","Al-Faisaly"],[7,"M. Al-Taamari","RW","Montpellier",1.3],[9,"A. Olwan","ST","Zakho",1.2],[17,"Y. Al-Naimat","LW","Al-Okhdood",1.1],
    [1,"A. Al-Fakhouri","GK","Al-Faisaly"],[22,"Y. Abu Layla","GK","Al-Hussein"],[12,"I. Haddad","RB","Al-Salt"],[13,"A. Haddad","CB","Al-Wehdat"],[14,"E. Al-Tamari","LB","Al-Ramtha"],[16,"R. Bani Attiah","CM","Al-Wehdat"],[10,"M. Daghan","CAM","Al-Faisaly"],[11,"M. Abu Zraiq","LW","Al-Hussein",1.1],[18,"A. Al-Sayed","RW","Al-Wehdat"],[19,"M. Khattab","ST","Al-Hussein"],[20,"S. Bani Yaseen","CB","Al-Faisaly"],
  ]],
  SRB: ["3-4-2-1", [
    [1,"V. Milinković-Savić","GK","Torino"],[4,"N. Milenković","CB","Nottingham Forest"],[6,"S. Pavlović","CB","Manchester Utd"],[3,"M. Veljković","CB","Celta Vigo"],[22,"A. Živković","RWB","PAOK"],[21,"N. Gudelj","CM","Sevilla"],[20,"S. Lukić","CM","Fulham"],[11,"F. Kostić","LWB","Juventus"],[10,"D. Tadić","CAM","Al-Wahda",1.2],[8,"S. Milinković-Savić","CAM","Al-Hilal",1.2],[9,"A. Mitrović","ST","Al-Hilal",1.3],
    [12,"P. Rajković","GK","Mallorca"],[23,"Đ. Petrović","GK","Bournemouth"],[5,"S. Eraković","CB","Rangers"],[15,"S. Babić","CB","Almería"],[2,"M. Stojković","RWB","Red Star"],[16,"S. Maksimović","CM","Panathinaikos"],[17,"I. Ilić","CM","Torino"],[18,"L. Samardžić","CAM","Atalanta",1.1],[7,"D. Vlahović","ST","Juventus",1.3],[14,"L. Jović","ST","AC Milan",1.1],[19,"V. Birmančević","RW","Sporting CP"],
  ]],
  NZL: ["4-3-3", [
    [1,"O. Sail","GK","Auckland City"],[2,"T. Bindon","CB","Nottingham Forest"],[5,"M. Boxall","CB","Minnesota Utd"],[6,"N. Pijnaker","CB","Hibernian"],[3,"L. Cacace","LB","Empoli"],[8,"J. Bell","CM","Viking"],[14,"M. Stamenic","CM","Olympiacos"],[10,"M. Garbett","CAM","Vejle"],[7,"B. Old","RW","St. Johnstone"],[9,"C. Wood","ST","Nottingham Forest",1.3],[11,"K. Barbarouses","LW","Sydney FC"],
    [12,"M. Crocombe","GK","Burton Albion"],[22,"A. Paulsen","GK","Brøndby"],[4,"F. Surman","CB","Portland Timbers"],[15,"S. Roux","RB","Macarthur"],[16,"T. Payne","RB","Wellington"],[17,"A. Rufer","CDM","Wellington"],[13,"M. Bevan","CM","Western Sydney"],[18,"S. Singh","CAM","Munich 1860",1.1],[19,"E. Just","RW","Vejle",1.1],[20,"B. Waine","ST","Shrewsbury"],[21,"C. Lewis","LB","Auckland City"],
  ]],
  AUS: ["4-3-3", [
    [1,"M. Ryan","GK","Roma"],[2,"N. Atkinson","RB","Hearts"],[19,"H. Souttar","CB","Sheffield Utd"],[4,"K. Rowles","CB","Hearts"],[16,"A. Behich","LB","Melbourne City"],[13,"A. O'Neill","CDM","Go Ahead Eagles"],[22,"J. Irvine","CM","St. Pauli",1.1],[8,"C. Metcalfe","CM","St. Pauli"],[7,"M. Leckie","RW","Melbourne City"],[9,"M. Duke","ST","Machida Zelvia",1.1],[10,"C. Goodwin","LW","Adelaide Utd",1.1],
    [18,"J. Gauci","GK","Aston Villa"],[12,"L. Thomas","GK","Melbourne Victory"],[3,"L. Miller","RB","Hibernian"],[5,"C. Burgess","CB","Ipswich Town"],[20,"T. Deng","CB","Albirex Niigata"],[15,"R. McGree","CAM","Middlesbrough"],[6,"K. Baccus","CM","Macarthur"],[23,"A. Hrustic","CM","Heracles"],[11,"K. Yengi","ST","Portsmouth",1.1],[17,"M. Boyle","RW","Hibernian"],[21,"S. Silvera","RW","Middlesbrough"],
  ]],
  CRC: ["4-3-3", [
    [1,"K. Navas","GK","Newell's Old Boys",1.1],[16,"C. Martínez","RB","Alajuelense"],[4,"K. Waston","CB","Saprissa"],[19,"K. Fuller","CB","Wolverhampton"],[8,"B. Oviedo","LB","Saprissa"],[5,"C. Borges","CDM","Saprissa"],[17,"Y. Tejeda","CM","Herediano"],[20,"B. Aguilera","CAM","Rosario Central"],[10,"J. Campbell","RW","Saprissa",1.2],[9,"M. Ugalde","ST","Spartak Moscow",1.2],[7,"A. Martínez","LW","New York City"],
    [18,"P. Sequeira","GK","Lugano"],[23,"E. Alpízar","GK","Alajuelense"],[3,"F. Calvo","CB","Konyaspor"],[15,"J. P. Vargas","CB","Millonarios"],[2,"J. Mora","LB","Saprissa"],[6,"O. Galo","CDM","Herediano"],[14,"O. Duarte","CB","Alajuelense"],[11,"J. Alcócer","RW","Westerlo",1.1],[12,"K. Vargas","ST","Hearts",1.1],[21,"A. Contreras","ST","Herediano"],[22,"C. Mora","RB","Saprissa"],
  ]],
  GHA: ["4-3-3", [
    [12,"L. Ati-Zigi","GK","St. Gallen"],[2,"T. Lamptey","RB","Brighton"],[5,"M. Salisu","CB","AS Monaco"],[18,"A. Djiku","CB","Fenerbahçe"],[3,"G. Mensah","LB","RC Lens"],[5,"E. Owusu","CDM","Lorient"],[14,"S. Abdul Samed","CM","RC Lens"],[10,"T. Partey","CM","Arsenal",1.2],[20,"M. Kudus","RW","Tottenham",1.4],[9,"I. Williams","ST","Athletic Club",1.3],[7,"K. Sulemana","LW","Southampton",1.2],
    [1,"J. Wollacott","GK","Crawley Town"],[22,"B. Nurudeen","GK","Asante Kotoko"],[4,"A. Seidu","RB","RC Strasbourg"],[15,"D. Amartey","CB","Besiktas"],[13,"B. Mensah","LB","Black Stars"],[8,"M. Ashimeru","CM","Anderlecht"],[6,"E. Lamptey","CDM","Almería"],[11,"A. Semenyo","RW","Bournemouth",1.1],[19,"E. Nuamah","LW","Lyon",1.1],[17,"J. Ayew","ST","Leicester City",1.1],[21,"F. Echara","ST","Hearts of Oak"],
  ]],
  PAN: ["4-3-3", [
    [1,"O. Mosquera","GK","Aris Limassol"],[16,"M. Murillo","RB","New York Red Bulls"],[5,"J. Córdoba","CB","Krasnodar"],[3,"F. Escobar","CB","Atlas"],[15,"E. Davis","LB","Differdange"],[6,"A. Godoy","CDM","San Jose"],[20,"A. Carrasquilla","CM","Houston Dynamo"],[8,"C. Martínez","CM","Atlético Nacional"],[7,"E. Bárcenas","RW","Mazatlán"],[9,"J. Fajardo","ST","Independiente",1.1],[19,"I. Díaz","LW","Querétaro",1.2],
    [22,"L. Mejía","GK","Universidad de Chile"],[12,"J. Saucedo","GK","Plaza Amador"],[2,"C. Blackman","RB","Sporting SM"],[4,"A. Andrade","CB","Tractor"],[23,"E. Bárcenas","LB","Tauro"],[13,"J. Welch","CB","Sporting SM"],[14,"C. Harvey","CM","Tauro"],[17,"J. Rodríguez","RW","CAI",1.1],[18,"C. Waterman","ST","Coquimbo Unido",1.1],[10,"E. Bárcenas","CAM","Mazatlán"],[21,"A. Murillo","LB","Plaza Amador"],
  ]],
  EGY: ["4-3-3", [
    [1,"M. El-Shenawy","GK","Al-Ahly"],[2,"M. Hany","RB","Al-Ahly"],[6,"A. Hegazi","CB","Al-Ittihad"],[3,"M. Abdelmonem","CB","Nice"],[12,"A. Fattouh","LB","Zamalek"],[17,"M. Elneny","CDM","Al-Jazira"],[8,"E. Ashour","CM","Al-Ahly"],[21,"T. Hamed","CM","Al-Wakrah"],[10,"M. Salah","RW","Liverpool",1.5],[9,"M. Mohamed","ST","Nantes",1.2],[14,"O. Marmoush","LW","Manchester City",1.3],
    [23,"M. Abou Gabal","GK","Al-Ahly"],[16,"M. Sobhi","GK","Pyramids"],[5,"A. Gabr","CB","Smouha"],[13,"O. Kamal","LB","Pyramids"],[15,"R. Nabil","RB","Al-Ahly"],[7,"Trezeguet","RW","Trabzonspor",1.2],[18,"A. El Soliya","CM","Al-Ahly"],[11,"M. Sherif","ST","Al-Ahly",1.1],[19,"I. Adel","CAM","Zamalek"],[20,"M. Shehata","RW","Al-Ahly"],[22,"A. Koka","LW","Zamalek"],
  ]],
  JAM: ["4-3-3", [
    [1,"A. Blake","GK","Philadelphia Union"],[2,"D. Lembikisa","RB","Wolverhampton"],[5,"E. Pinnock","CB","Brentford"],[15,"M. Hector","CB","free agent"],[3,"G. Leigh","LB","Hull City"],[8,"B. De Cordova-Reid","CM","Leicester City"],[6,"J. Latibeaudiere","CDM","Coventry City"],[10,"K. Palmer","CAM","Coventry City"],[7,"D. Gray","RW","Al-Ettifaq",1.2],[9,"M. Antonio","ST","West Ham",1.2],[11,"L. Bailey","LW","Aston Villa",1.3],
    [12,"J. Waite","GK","Forest Green"],[22,"C. McCammon","GK","Charlotte"],[4,"D. Lowe","CB","Houston Dynamo"],[16,"A. King","RB","Leyton Orient"],[13,"R. Williams","LB","Bristol City"],[14,"K. Lawrence","CM","Mazatlán"],[17,"D. Gardner","CM","Sheffield Wednesday"],[18,"S. Nicholson","ST","Spartak Trnava",1.1],[19,"T. Decordova","RW","Cavalier"],[20,"R. Russell","LW","St. Louis City"],[21,"J. Pierre","ST","Detroit City"],
  ]],
  CIV: ["4-3-3", [
    [16,"Y. Fofana","GK","Angers"],[2,"S. Aurier","RB","free agent"],[4,"E. Ndicka","CB","Roma"],[22,"O. Kossounou","CB","Atalanta"],[3,"G. Konan","LB","Al-Ettifaq"],[6,"S. Fofana","CDM","Al-Nassr"],[19,"I. Sangaré","CM","Nottingham Forest"],[8,"F. Kessié","CM","Al-Ahli",1.2],[10,"N. Pépé","RW","Villarreal",1.2],[9,"S. Haller","ST","Leganés",1.2],[11,"S. Adingra","LW","Sunderland",1.1],
    [1,"B. A. Sangaré","GK","Sevilla"],[23,"M. Diakité","GK","ASEC Mimosas"],[5,"W. Singo","RB","AS Monaco"],[12,"W. Boly","CB","Al-Shabab"],[15,"O. Diomandé","CB","Sporting CP"],[13,"J. M. Seri","CM","Hull City"],[17,"I. Diallo","RW","Amiens"],[7,"A. Diallo","RW","Manchester Utd",1.3],[20,"C. Kouamé","ST","Fiorentina",1.1],[18,"J. Bamba","LW","RC Lens",1.1],[14,"M. Cornet","RW","West Ham"],
  ]],
  PAR: ["4-3-3", [
    [1,"A. Silva","GK","Club Libertad"],[4,"G. Velázquez","CB","Club Libertad"],[2,"F. Balbuena","CB","Internacional"],[3,"O. Alderete","CB","Sunderland"],[6,"J. Alonso","LB","Krasnodar"],[5,"A. Cubas","CDM","Vancouver"],[15,"M. Villasanti","CM","Grêmio"],[8,"D. Bobadilla","CM","San Lorenzo"],[10,"M. Almirón","RW","Atlanta Utd",1.2],[19,"A. Sanabria","ST","Cruzeiro",1.2],[11,"J. Enciso","LW","Ipswich Town",1.2],
    [12,"R. Fernández","GK","Bahia"],[22,"G. Aguilar","GK","Cerro Porteño"],[13,"J. Cáceres","RB","Cerro Porteño"],[16,"A. Sández","LB","Boca Juniors"],[14,"R. Rojas","RB","Talleres"],[17,"R. Sosa","RW","Nottingham Forest",1.1],[7,"D. Gómez","CM","Inter Miami",1.1],[18,"M. Bareiro","ST","San Lorenzo",1.1],[20,"O. Bobadilla","CAM","River Plate"],[9,"G. Ávalos","ST","Independiente"],[21,"B. Ovelar","RW","Olimpia"],
  ]],
  TUN: ["4-3-3", [
    [16,"A. Dahmen","GK","Sporting Charleroi"],[12,"M. Dräger","RB","FC Augsburg"],[3,"M. Talbi","CB","Lorient"],[2,"Y. Meriah","CB","Esperance"],[20,"A. Abdi","LB","Caen"],[15,"A. Laïdouni","CDM","Stade Rennais"],[13,"F. Sassi","CM","Al-Arabi"],[10,"H. Mejbri","CAM","Burnley",1.2],[7,"Y. Msakni","RW","Al-Arabi",1.2],[9,"S. Jaziri","ST","Esperance",1.1],[11,"N. Sliti","LW","Al-Ettifaq",1.1],
    [1,"M. Hassen","GK","Club Africain"],[22,"B. Ben Saïd","GK","US Monastir"],[5,"D. Bronn","CB","Salernitana"],[6,"W. Kechrida","RB","Hatayspor"],[4,"M. Bourhane","CB","Esperance"],[8,"E. Skhiri","CM","Eintracht Frankfurt",1.1],[14,"A. Ben Slimane","CM","Hannover"],[17,"E. Achouri","RW","Copenhagen",1.1],[18,"O. Layouni","LW","Servette"],[19,"H. Rafia","CAM","Lugano"],[21,"S. Mestouri","RB","Le Havre"],
  ]],
  VEN: ["4-3-3", [
    [1,"R. Romo","GK","Tigre"],[4,"J. Aramburu","RB","Real Sociedad"],[3,"Y. Osorio","CB","Parma"],[2,"N. Ferraresi","CB","São Paulo"],[14,"M. Navarro","LB","Talleres"],[5,"J. Martínez","CDM","Philadelphia Union"],[6,"T. Rincón","CM","Santos"],[8,"Y. Herrera","CM","Girona",1.2],[7,"J. Savarino","RW","Botafogo",1.2],[9,"S. Rondón","ST","Pachuca",1.2],[11,"Y. Soteldo","LW","Santos",1.2],
    [12,"J. Graterol","GK","Caracas"],[22,"W. Faríñez","GK","Lens"],[13,"W. Ángel","CB","Apertura"],[15,"A. González","RB","Deportivo Táchira"],[16,"C. Cásseres","CM","Toulouse"],[17,"D. Pereira","CM","Casa Pia"],[10,"E. Soto","CAM","Tigres",1.1],[18,"D. Machís","LW","Anorthosis",1.1],[19,"E. Bello","RW","Lokomotiv Moscow",1.1],[20,"J. Martínez","ST","CF Montréal",1.1],[21,"K. Rodríguez","RW","Banfield"],
  ]],
  UKR: ["4-3-3", [
    [1,"A. Trubin","GK","Benfica"],[22,"O. Tymchyk","RB","Dynamo Kyiv"],[13,"I. Zabarnyi","CB","Bournemouth",1.1],[3,"M. Matviyenko","CB","Shakhtar"],[16,"V. Mykolenko","LB","Everton"],[5,"T. Stepanenko","CDM","Al-Ittihad"],[17,"O. Zinchenko","CM","Arsenal",1.1],[10,"H. Sudakov","CAM","Benfica",1.2],[7,"V. Tsyhankov","RW","Girona",1.1],[9,"A. Dovbyk","ST","Roma",1.3],[11,"M. Mudryk","LW","Chelsea",1.2],
    [12,"A. Lunin","GK","Real Madrid"],[23,"D. Riznyk","GK","Shakhtar"],[2,"Y. Konoplya","RB","Shakhtar"],[4,"M. Talovierov","CB","Shakhtar"],[6,"T. Yarmolenko","RW","Dynamo Kyiv",1.1],[8,"R. Malinovskyi","CAM","Genoa",1.2],[14,"M. Shaparenko","CM","Dynamo Kyiv"],[18,"O. Zubkov","LW","Trabzonspor",1.1],[19,"R. Yaremchuk","ST","Olympiacos",1.1],[20,"V. Vanat","ST","Dynamo Kyiv",1.1],[21,"O. Brazhko","CM","Dynamo Kyiv"],
  ]],
  IRQ: ["4-2-3-1", [
    [1,"J. Hassan","GK","Al-Quwa Al-Jawiya"],[2,"M. Doski","RB","Duhok"],[4,"R. Sulaka","CB","Western Sydney"],[5,"A. Hashim","CB","Al-Shorta"],[3,"H. Ali","LB","Al-Shorta"],[6,"A. Al-Ammari","CDM","Mjällby"],[8,"B. Resan","CM","Al-Shorta"],[7,"I. Bayesh","RW","Al-Quwa Al-Jawiya"],[10,"Z. Iqbal","CAM","Utrecht",1.2],[11,"A. Jasim","LW","Al-Zawraa",1.1],[9,"A. Hussein","ST","Al-Qadsiah",1.2],
    [12,"A. Basil","GK","Al-Shorta"],[22,"F. Talib","GK","Al-Quwa Al-Jawiya"],[13,"M. Nadhim","CB","Al-Shorta"],[14,"M. Younis","CB","Al-Najaf"],[15,"S. Sabah","RB","Al-Karkh"],[16,"A. Faez","CM","Al-Shorta"],[17,"S. Kareem","RW","Erbil",1.1],[18,"M. Ali","ST","Al-Duhail",1.2],[19,"A. Al-Hamadi","ST","Ipswich Town",1.1],[20,"H. Tahir","LM","Al-Quwa Al-Jawiya"],[21,"K. Dawood","CB","Al-Shorta"],
  ]],
  AUT: ["4-2-3-1", [
    [1,"P. Pentz","GK","Brøndby"],[2,"S. Posch","RB","Bologna"],[15,"P. Lienhart","CB","Freiburg"],[4,"K. Danso","CB","Tottenham"],[16,"P. Mwene","LB","Mainz"],[6,"N. Seiwald","CDM","RB Leipzig"],[8,"K. Laimer","CM","Bayern Munich"],[19,"C. Baumgartner","RW","RB Leipzig",1.2],[10,"M. Sabitzer","CAM","Borussia Dortmund",1.2],[9,"M. Gregoritsch","LW","Freiburg",1.1],[7,"M. Arnautović","ST","free agent",1.2],
    [12,"H. Lindner","GK","Union Berlin"],[23,"N. Hedl","GK","Rapid Wien"],[3,"M. Wöber","CB","Borussia M'gladbach"],[5,"G. Trauner","CB","Feyenoord"],[17,"F. Wimmer","RW","Wolfsburg",1.1],[13,"F. Grillitsch","CM","Hoffenheim"],[14,"R. Schmid","CM","Werder Bremen"],[20,"K. Schmidt","RB","RB Leipzig"],[11,"M. Entrup","ST","Hartberg",1.1],[18,"R. Sabitzer","RW","Lustenau"],[21,"A. Schöpf","CAM","SCR Altach"],
  ]],
  CMR: ["4-3-3", [
    [1,"A. Onana","GK","Manchester Utd",1.1],[2,"C. Fai","RB","free agent"],[4,"C. Wooh","CB","Stade Rennais"],[3,"J. Castelletto","CB","Nantes"],[14,"N. Tolo","LB","Seattle Sounders"],[8,"A. Zambo Anguissa","CDM","Napoli",1.2],[18,"M. Hongla","CM","Granada"],[6,"C. Baleba","CM","Brighton",1.2],[7,"B. Mbeumo","RW","Manchester Utd",1.3],[10,"V. Aboubakar","ST","Neftçi",1.2],[12,"K. Toko Ekambi","LW","Abha",1.1],
    [16,"D. Epassy","GK","Abha"],[23,"F. Ondoa","GK","Sabail"],[5,"E. Ebosse","CB","Udinese"],[15,"J. Tchamadeu","RB","Stoke City"],[13,"O. Mbaizo","RB","Philadelphia Union"],[17,"P. Kunde","CM","Olympiacos"],[19,"F. Magri","CAM","Toulouse",1.1],[20,"G. Nkoudou","LW","Damac",1.1],[9,"C. Bassogog","RW","Aris",1.1],[11,"S. Magnetti","CM","Antalyaspor"],[21,"J. Onana","CDM","Lyon"],
  ]],
  NOR: ["4-3-3", [
    [12,"Ø. Nyland","GK","Sevilla"],[2,"J. Ryerson","RB","Borussia Dortmund"],[5,"K. Ajer","CB","Brentford"],[6,"L. Østigård","CB","Stade Rennais"],[3,"B. Meling","LB","Stade Rennais"],[8,"S. Berge","CDM","Fulham"],[18,"F. Aursnes","CM","Benfica"],[20,"M. Ødegaard","CM","Arsenal",1.3],[7,"A. Nusa","RW","RB Leipzig",1.2],[9,"E. Haaland","ST","Manchester City",1.6],[11,"A. Sørloth","LW","Atlético Madrid",1.3],
    [1,"E. Selvik","GK","Brann"],[22,"M. Dyngeland","GK","Brann"],[4,"M. Høibråten","CB","Union Berlin"],[15,"D. M. Wolfe","LB","Nice"],[13,"A. Heggem","CB","Bologna"],[16,"P. Berg","CM","Bodø/Glimt"],[17,"O. Bobb","RW","Manchester City",1.1],[14,"J. Strand Larsen","ST","Wolverhampton",1.2],[19,"O. Solbakken","LW","Olympiacos",1.1],[10,"K. Thorsby","CM","Genoa"],[21,"H. Nordås","CM","Brann"],
  ]],
  ALG: ["4-3-3", [
    [1,"A. Mandrea","GK","AS Monaco"],[2,"Y. Atal","RB","Al-Sadd"],[5,"A. Mandi","CB","Lille"],[15,"M. Tougai","CB","Espérance"],[3,"R. Bensebaïni","LB","Borussia Dortmund",1.1],[8,"N. Bentaleb","CDM","Angers"],[13,"R. Zerrouki","CM","Feyenoord"],[6,"I. Bennacer","CM","AC Milan",1.2],[7,"R. Mahrez","RW","Al-Ahli",1.3],[9,"B. Bounedjah","ST","Al-Sadd",1.2],[11,"A. Gouiri","LW","Marseille",1.2],
    [16,"A. Oukidja","GK","Saint-Étienne"],[23,"L. Zidane","GK","Granada"],[4,"A. Touba","CB","Trabzonspor"],[12,"J. Hadjam","LB","Young Boys"],[14,"H. Aouar","CAM","Roma",1.1],[17,"A. Ounas","RW","Lille",1.1],[18,"M. Amoura","ST","Wolfsburg",1.2],[10,"S. Benrahma","LW","Neom",1.1],[19,"I. Slimani","ST","Mechelen",1.1],[20,"F. Chaïbi","CAM","Eintracht Frankfurt"],[21,"H. Boudaoui","CM","Nice"],
  ]],
  TUR: ["4-2-3-1", [
    [1,"M. Günok","GK","Besiktas"],[2,"Z. Çelik","RB","AS Roma"],[3,"M. Demiral","CB","Al-Ahli"],[4,"A. Bardakcı","CB","Galatasaray"],[20,"F. Kadıoğlu","LB","Inter"],[8,"S. Özcan","CDM","Borussia Dortmund"],[7,"İ. Yüksek","CM","Fenerbahçe"],[15,"K. Yıldız","RW","Juventus",1.3],[10,"H. Çalhanoğlu","CAM","Inter",1.3],[17,"K. Aktürkoğlu","LW","Benfica",1.2],[9,"B. A. Yılmaz","ST","Galatasaray",1.1],
    [12,"U. Çakır","GK","Galatasaray"],[23,"A. Bayındır","GK","Manchester Utd"],[5,"M. Müldür","RB","Sassuolo"],[14,"S. Akaydın","CB","Montpellier"],[16,"O. Kökçü","CM","Benfica",1.1],[6,"O. Ayhan","CDM","Galatasaray"],[18,"A. Güler","CAM","Real Madrid",1.3],[11,"Y. Yazıcı","RW","Hull City",1.1],[19,"C. Tosun","ST","Besiktas",1.1],[21,"S. Kılıçsoy","ST","Besiktas",1.1],[22,"E. Yıldız","LW","Galatasaray"],
  ]],

  });
})();
